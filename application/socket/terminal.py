# -*- coding: utf-8 -*-

import paramiko
from socket import error
from paramiko import channel
from flask import request, Blueprint
from flask_socketio import Namespace, emit

from application import socketIO
from setting.const import HOST, USER, PASSWORD
from paramiko import BadHostKeyException, AuthenticationException, SSHException

terminal = Blueprint("terminal", __name__)

chan_active_dict = {}
client_dict = {}


def send_result(sid):
    while True:
        socketIO.sleep(0.01)
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
                    socketIO.emit("result", {"result": data}, namespace="/terminal")
            except:
                continue
        else:
            socketIO.emit("exit", {"sid": sid}, namespace="/terminal")
            del chan_active_dict[sid]
            break


class TerminalHandler(Namespace):
    @staticmethod
    def on_connect():
        client = paramiko.SSHClient()
        try:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname=HOST, port=22, username=USER, password=PASSWORD)
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
                socketIO.start_background_task(send_result, sid)
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


socketIO.on_namespace(TerminalHandler("/terminal"))
