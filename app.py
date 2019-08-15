import random
import json

from flask_socketio import SocketIO, Namespace, emit, join_room, leave_room, close_room
from flask import Flask, render_template, request
import paramiko
from paramiko import BadHostKeyException, AuthenticationException, SSHException
from socket import error
from paramiko import channel

app = Flask(__name__)
app.secret_key = "hello"
app.config.update(HOST="192.168.112.131")
socket = SocketIO(app, path="/share/socket.io")

connect = None
chan_active_dict = {}
client_dict = {}


@app.route("/", methods=["GET"])
def socket_con():
    return render_template("index.html")


@app.route("/terminal")
def terminal_con():
    return render_template("terminal.html")


def send_num():
    while True:
        socket.sleep(1)
        if connect:
            num = random.randint(10, 99)
            socket.emit("result", str(num), namespace="/share")
        else:
            break
        # num = random.randint(0, 9)
        # socket.emit("result", str(num), namespace="/share")


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
            client.connect(hostname=app.config.get("HOST"), port=22, username="xiaobin", password='xiao')
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
    print(app.static_folder)
    socket.run(app, host="127.0.0.1", port=9999, debug=True)


