import codecs
import os

from setuptools import setup, find_packages

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
PROJECT_NAME = "medusa"
PROJECT_PATH = CURRENT_DIR + "/" + PROJECT_NAME


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), "r") as fp:
        return fp.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


def get_version_from_init():
    return get_version(f"{PROJECT_PATH}/__init__.py")


setup(
    name=PROJECT_NAME,
    version=get_version_from_init(),
    python_requires="~=3.10",
    packages=find_packages(),
    requires=["setuptools"],
    entry_points={
        "console_scripts": [
            f"medusa = {PROJECT_NAME}.__main__:main",
        ]
    },
    install_requires=["requests==2.31.0", "pyyaml==6.0"],
    package_dir={"": "."},
    package_data={
        f"{PROJECT_NAME}.configs": ["*.yml"],
    },
    include_package_data=True,
)
