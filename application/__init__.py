import logging
from flask import Flask
from flask_socketio import SocketIO

from setting import AppConfig
from setting.const import SOCKET_PATH
from logging.handlers import RotatingFileHandler


socketIO = SocketIO()


def log_config(cfg="dev"):
    """
    :param cfg: configuration name
    :param app: application
    :return: log app
    """
    logger = logging.getLogger("app")
    handler = RotatingFileHandler("log/app.log", maxBytes=1024 * 1024 * 10, backupCount=10, encoding="utf-8")
    cfg_obj = AppConfig.get(cfg).LOG_LEVEL if cfg in AppConfig else AppConfig.get("dev").LOG_LEVEL
    handler.setLevel(cfg_obj)
    fmt = logging.Formatter("%(levelname)s: [%(asctime)s][%(pathname)s][%(funcName)s] %(lineno)s {%(message)s}")
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    return logger


def create_app(cfg="dev"):
    """
    create application
    :param cfg: configuration name
    :return: application
    """
    app = Flask(__name__)
    cf_obj = AppConfig.get(cfg) if cfg in AppConfig else AppConfig.get("dev")
    app.config.from_object(cf_obj)
    socketIO.init_app(app, path=SOCKET_PATH)
    app.logger = log_config(cfg)
    print(f"\n{'*'*100}\ncreate app success\nuse configuration {cf_obj.__name__}")

    # 注册蓝图
    from application.index import index
    from application.file import files
    from application.socket import terminal

    app.register_blueprint(files)
    app.register_blueprint(index)
    app.register_blueprint(terminal)
    return app


