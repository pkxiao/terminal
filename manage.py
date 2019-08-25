import sys

from application import create_app, socketIO
from flask_script import Manager


if __name__ == '__main__':
    if sys.argv.__len__() > 1:
        cfg = sys.argv[1]
    else:
        cfg = "dev"
    app = create_app(cfg)
    manger = Manager(app)
    manger.add_command("run", socketIO.run(app, host="127.0.0.1", port=9999))


