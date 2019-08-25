# -*- coding: utf-8 -*-

import os
# import sys
import time
import socket
import platform


def get_system_info():
    """获取本机系统版本"""
    return platform.system()


def get_file_sep():
    """获取文件分割符"""
    return os.sep


def get_host():
    """获取本机ip"""
    return socket.gethostbyname(socket.getfqdn(socket.gethostname()))


def get_now_time(fmt="%Y-%m-%d %H:%M:%S", sec=time.time()):
    """
    获取格式化时间
    :param fmt: string format
    :param sec: Timestamp
    :return: string time
    """
    return time.strftime(fmt, time.localtime(sec))


def get_system_root():
    """获取根目录"""
    path = os.getenv("HOMEDRIVE")
    if not path:
        return get_file_sep()
    return path


if __name__ == '__main__':
    # 获取本机电脑名
    # print(get_system_info())
    # print(get_file_sep())
    # print(get_host())
    # print(get_now_time())
    print(get_system_root())
    pass
    # print(os.getenv("HOMEDRIVE"))
