import os
from functools import cache

import yaml


CONFIG_DIR = f"{os.path.dirname(__file__)}/configs"


@cache
def __config(path: str):
    with open(path, "r") as f:
        return yaml.load(f, yaml.FullLoader)


def config(file: str = "config"):
    return __config(f"{CONFIG_DIR}/{file}.yml")


@cache
def __template(path: str):
    with open(path, "r") as f:
        return f.readlines()


def template(backend: str):
    return __template(f"{CONFIG_DIR}/{backend}_template.conf")
