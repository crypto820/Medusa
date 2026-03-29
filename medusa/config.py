import os
from functools import cache

import yaml


CONFIG_DIR = f"{os.path.dirname(__file__)}/configs"


def _config_path(file: str) -> str:
    if os.path.isabs(file):
        return file
    if not file.endswith(".yml"):
        file = f"{file}.yml"
    return f"{CONFIG_DIR}/{file}"


@cache
def __config(path: str):
    with open(path, "r") as f:
        return yaml.load(f, yaml.FullLoader)


def config(file: str = "config.yml"):
    return __config(_config_path(file))


@cache
def __template(path: str):
    with open(path, "r") as f:
        return f.readlines()


def template(backend: str):
    return __template(f"{CONFIG_DIR}/{backend}_template.conf")
