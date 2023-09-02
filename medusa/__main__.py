import argparse
import logging
import base64
from functools import reduce
from typing import List

import requests
from urllib.parse import urlparse, ParseResult

from medusa.config import config, template
from medusa.subconverter import SubConverter


def setup_logger():
    logging.basicConfig(level=logging.INFO,
                        format="[%(asctime)s] [%(levelname)s] - %(message)s - [%(filename)s:%(lineno)d]",
                        datefmt="%Y-%m-%d %H:%M:%S")


def fetch_config(url: str) -> List[ParseResult]:
    logging.info(f"Handling subscription {url}")
    b64 = requests.get(url)
    hosts = base64.b64decode(b64.content).decode().splitlines(keepends=False)
    print(hosts[0])
    return [urlparse(host) for host in hosts if len(host)]


def main():
    setup_logger()
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", type=str, required=True)
    parser.add_argument("--backend", type=str, required=False, default="glider")
    args = parser.parse_args()
    pr_list = list()
    for url in config()["subscriptions"]:
        results = fetch_config(url)
        pr_list.append(SubConverter.convert(args.backend, results))

    result = list(map(lambda e: f"{e}\n", reduce(list.__add__, pr_list)))
    with open(args.output, "w") as f:
        content = template(args.backend)
        f.writelines(content)
        f.writelines(result)
    return


if __name__ == "__main__":
    exit(main())
