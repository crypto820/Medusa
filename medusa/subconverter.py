import base64
import logging
from typing import Literal, List
from urllib.parse import ParseResult, unquote, parse_qs


def b64decode_urlsafe(s: str) -> str:
    missing_padding = len(s) % 4
    if missing_padding != 0:
        s += '=' * (4 - missing_padding)
    return base64.urlsafe_b64decode(s).decode()


class SubConverter:
    @staticmethod
    def convert(backend: str, parse_results: List[ParseResult]):
        match backend:
            case "glider":
                return SubConverter._to_glider(parse_results)
            case _:
                raise NotImplementedError

    @staticmethod
    def _to_glider(parse_results: List[ParseResult]):
        def handle_ss(ss: ParseResult):
            return ''.join(("forward=",
                            ss.scheme, "://",
                            b64decode_urlsafe(ss.username), "@",
                            ss.hostname, ":",
                            str(ss.port), "#",
                            unquote(ss.fragment)))

        def handle_trojan(tj: ParseResult):
            return ''.join(("forward=",
                            tj.scheme, "://",
                            tj.username, "@",
                            tj.hostname, ":",
                            str(tj.port), "?",
                            f"serverName={parse_qs(tj.query)['sni']}",
                            "&skip-cert-verify=true",
                            "#", unquote(tj.fragment)))

        res = list()
        for r in parse_results:
            logging.info(f"Handling {r}")
            pr = eval(f"handle_{r.scheme}")(r)
            logging.info(f"Constructed '{pr}'")
            res.append(pr)
        return res
