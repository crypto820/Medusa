import argparse
import base64
import binascii
import logging
from typing import Dict, List
from urllib.parse import urlparse, ParseResult

from medusa.clash import forwards_from_clash
from medusa.config import config, template
from medusa.subconverter import SubConverter


def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] - %(message)s - [%(filename)s:%(lineno)d]",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def decode_base64(payload: str) -> str:
    compact_payload = "".join(payload.split())
    if not compact_payload:
        return ""

    missing_padding = len(compact_payload) % 4
    if missing_padding:
        compact_payload += "=" * (4 - missing_padding)

    for altchars in (None, b"-_"):
        try:
            return base64.b64decode(
                compact_payload, altchars=altchars, validate=True
            ).decode()
        except (binascii.Error, UnicodeDecodeError):
            continue

    raise ValueError("Invalid base64 subscription configured in the selected config file")


def load_config(config_name: str) -> Dict:
    cfg = config(config_name)
    return cfg or {}


def load_subscriptions(cfg: Dict) -> List[str]:
    subscriptions = cfg.get("subscriptions_base64", cfg.get("subscriptions", []))

    if isinstance(subscriptions, str):
        return [subscriptions]

    res = []
    for entry in subscriptions:
        if isinstance(entry, dict):
            entry = entry.get("base64")
        if not isinstance(entry, str):
            raise TypeError(
                "Each subscription must be a base64 string or a dict with a 'base64' field"
            )
        res.append(entry)
    return res


def fetch_config(subscription: str, index: int) -> List[ParseResult]:
    logging.info(f"Handling subscription #{index} from config")
    hosts = decode_base64(subscription).splitlines(keepends=False)
    return [urlparse(host) for host in hosts if len(host)]


def main():
    setup_logger()
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", type=str, required=True)
    parser.add_argument("--backend", type=str, required=False, default="glider")
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        required=False,
        help="Config filename or path. Defaults to medusa/configs/config.yml",
    )
    parser.add_argument(
        "--clash",
        type=str,
        required=False,
        help="Path to a clash.yaml file to convert directly into the selected backend",
    )
    args = parser.parse_args()

    if args.config and args.clash:
        parser.error("--config and --clash are mutually exclusive")

    if args.clash:
        result = [f"{entry}\n" for entry in forwards_from_clash(args.clash, args.backend)]
    else:
        cfg = load_config(args.config or "config.yml")
        pr_list = list()
        for index, subscription in enumerate(load_subscriptions(cfg), start=1):
            results = fetch_config(subscription, index)
            pr_list.append(SubConverter.convert(args.backend, results))
        result = [f"{entry}\n" for entries in pr_list for entry in entries]

    with open(args.output, "w") as f:
        content = list(template(args.backend))
        if content:
            if not content[-1].endswith("\n"):
                content[-1] = f"{content[-1]}\n"
            content.append("\n")
        f.writelines(content)
        f.writelines(result)
    return


if __name__ == "__main__":
    exit(main())
