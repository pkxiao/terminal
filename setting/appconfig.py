# -*- coding: utf-8 -*-

import logging

import random_string


class _BaseConfig:
    SECRET_KEY = random_string.generate(10)


class Production(_BaseConfig):
    LOG_LEVEL = logging.ERROR
    DEBUG = False


class Development(_BaseConfig):
    LOG_LEVEL = logging.DEBUG
    DEBUG = True


AppConfig = {
    "dev": Development,
    "pro": Production
}