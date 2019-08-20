import random
import os
import traceback
import time
import sys

from flask_socketio import SocketIO, Namespace, emit
from flask import Flask, render_template, request, jsonify, current_app
import paramiko
from paramiko import BadHostKeyException, AuthenticationException, SSHException
from socket import error
from paramiko import channel

app = Flask(__name__)
app.secret_key = "hello"
app.config.update(HOST="192.168.112.132", PASSWORD="xiao", USER="xiaobin")
socket = SocketIO(app, path="/share/socket.io")

connect = None
chan_active_dict = {}
client_dict = {}
init_path = "c:" if sys.platform == "win32" else "/"


@app.route("/", methods=["GET"])
def socket_con():
    return render_template("index.html")


@app.route("/file/list", methods=["GET"])
def file_list():
    filename = request.args.get("filename", init_path).strip()
    if not os.path.exists(filename):
        return jsonify(code=3, msg=f"{filename}目录不存在")
    dir_list = os.listdir(filename)
    dir_length = len(dir_list)
    if dir_length <= 0:
        return jsonify(code=0, msg=[])
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
    return jsonify(code=0, results=(d_list+f_list), total=dir_length, msg="")


def send_num():
    while True:
        socket.sleep(1)
        if connect:
            num = random.randint(10, 99)
            socket.emit("result", str(num), namespace="/share")
        else:
            break


class NamespaceHandler(Namespace):
    @staticmethod
    def on_get():
        global connect
        if connect:
            return False
        connect = True
        socket.start_background_task(send_num)

    @staticmethod
    def on_disconnect():
        global connect
        connect = False
        print("关闭")


def send_result(sid):
    while True:
        socket.sleep(0.01)
        if sid not in chan_active_dict:
            break
        chan = chan_active_dict[sid]  # type: channel.Channel
        if not chan.active:
            del chan_active_dict[sid]
            break
        if not chan.exit_status_ready():
            try:
                data = chan.recv(1024)
                if data:
                    data = data.decode("utf-8")
                    socket.emit("result", {"result": data}, namespace="/terminal")
            except:
                continue
        else:
            socket.emit("exit", {"sid": sid}, namespace="/terminal")
            del chan_active_dict[sid]
            break


class TerminalHandler(Namespace):
    @staticmethod
    def on_connect():
        client = paramiko.SSHClient()
        try:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname=app.config.get("HOST"), port=22, username=app.config.get("USER"),
                           password=app.config.get("PASSWORD"))
            chan = client.invoke_shell("vt100")  # type: channel.Channel
            chan.settimeout(0)
            sid = request.sid
            chan_active_dict[sid] = chan
            client_dict.update({sid: client})
            emit("login", {"code": 0, "sid": sid})
        except BadHostKeyException as ex:
            emit("login", {"code": 3, "msg": str(ex)})
        except AuthenticationException as ex:
            emit("login", {"code": 3, "msg": str(ex)})
        except SSHException as ex:
            emit("login", {"code": 3, "msg": str(ex)})
        except error as ex:
            emit("login", {"code": 3, "msg": str(ex)})
        except Exception as ex:
            emit("login", {"code": 3, "msg": str(ex)})

    @staticmethod
    def on_grs(data):
        sid = data.get("sid")
        if sid in chan_active_dict:
            chan = chan_active_dict[sid]  # type: channel.Channel
            if chan.active:
                socket.start_background_task(send_result, sid)
            else:
                del chan_active_dict[sid]

    @staticmethod
    def on_input(data):
        sid = data.get("sid")
        ipt = data.get("input")
        if sid in chan_active_dict:
            chan = chan_active_dict[sid]  # type: channel.Channel
            if chan.active:
                chan.send(ipt)
            else:
                del chan_active_dict[sid]

    @staticmethod
    def on_resize(data):
        sid = data.get("sid")
        if sid in chan_active_dict:
            chan = chan_active_dict[sid]  # type: channel.Channel
            if chan.active:
                rows = data.get("rows")
                cols = data.get("cols")
                # print(cols)
                chan.resize_pty(width=int(cols), height=int(rows))
            else:
                del chan_active_dict[sid]

    @staticmethod
    def on_close(data):
        sid = data.get("sid")
        if sid in chan_active_dict:
            chan = chan_active_dict[sid]
            chan.close()
            del chan_active_dict[sid]
        try:
            client = client_dict.pop(sid)
            if client:
                client.close()
        except KeyError:
            pass
        finally:
            return True


socket.on_namespace(NamespaceHandler("/share"))
socket.on_namespace(TerminalHandler("/terminal"))

if __name__ == '__main__':
    socket.run(app, host="127.0.0.1", port=9999, debug=True)
