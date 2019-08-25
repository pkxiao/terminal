# -*- coding: utf-8 -*-
import os
import time
import traceback

from flask import Blueprint, request, jsonify, current_app, send_file

from libs.utils import get_file_sep, get_system_root


files = Blueprint("file", __name__, url_prefix="/file")


init_path = get_system_root()
sep = get_file_sep()


@files.route("/list", methods=["GET"])
def file_list():
    filename = request.args.get("path", init_path).strip()
    if not os.path.exists(filename):
        return jsonify(code=3, msg=f"{filename}目录不存在")
    if not os.path.isdir(filename):
        return jsonify(code=3, msg=f"{filename}是个文件")
    dir_list = os.listdir(filename)
    dir_length = len(dir_list)
    if dir_length <= 0:
        return jsonify(code=0, results=[], total=dir_length, path=filename, sep=sep, msg="")
    try:
        page = int(request.args.get("page", "1").strip())
        page_size = int(request.args.get("per_page", "10").strip())
        dir_list.sort(key=lambda x: os.path.getmtime(os.path.join(filename, x)), reverse=True)
        if page_size * page <= dir_length:
            current_list = dir_list[(page - 1) * page_size:page * page_size]
        else:
            current_list = dir_list[(page - 1) * page_size:]
    except Exception as ex:
        current_app.logger.error(f"{filename}分页查询失败:\n{traceback.format_exc()}")
        return jsonify(code=3, msg=str(ex))
    d_list, f_list = [], []
    for file in current_list:
        file_path = os.path.join(filename, file)
        item = {
            "name": file,
            "path": file_path,
            "size": str(os.path.getsize(file_path)//1024) + "k",
            "mtime": time.strftime("%y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(file_path))),
            "ctime": time.strftime("%y-%m-%d %H:%M:%S", time.localtime(os.path.getctime(file_path))),
            "type": "file",
        }
        if os.path.isdir(file_path):
            item.update(type="dir")
            d_list.append(item)
        else:
            f_list.append(item)
    return jsonify(code=0, results=(d_list+f_list), total=dir_length, path=filename, sep=sep, msg="")


@files.route("/visit", methods=["GET"])
def file_visit():
    filename = request.args.get("path", "").strip()
    page = int(request.args.get("page", "1").strip())
    page_size = int(request.args.get("size", "1024").strip())
    if not filename:
        return jsonify(code=3, msg="不知道看什么")
    if not os.path.exists(filename):
        return jsonify(code=3, msg="文件不存在")
    item = {}
    try:
        file_size = os.path.getsize(filename)
        with open(filename, "r") as f:
            f.seek((page-1)*page_size, 0)
            data = f.read(page_size)
        # try:
        #     data = data.decode("utf-8")
        # except:
        #     data = data.decode("gbk")
            item.update(total=file_size, data=data)
    except Exception as ex:
        current_app.logger.error(traceback.format_exc())
        return jsonify(code=3, msg=str(ex))
    return jsonify(code=0, results=item, msg="")
