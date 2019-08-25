# -*- coding: utf-8 -*-
import random

from flask import Blueprint, render_template
from flask_socketio import Namespace

from application import socketIO

index = Blueprint("index", __name__)
connect = None


@index.route("/", methods=["GET"])
def socket_con():
    return render_template("index.html")


def send_num():
    while True:
        socketIO.sleep(1)
        if connect:
            num = random.randint(10, 99)
            socketIO.emit("result", str(num), namespace="/share")
        else:
            break


class NamespaceHandler(Namespace):
    @staticmethod
    def on_get():
        global connect
        if connect:
            return False
        connect = True
        socketIO.start_background_task(send_num)

    @staticmethod
    def on_disconnect():
        global connect
        connect = False
        print("关闭")


socketIO.on_namespace(NamespaceHandler("/share"))
