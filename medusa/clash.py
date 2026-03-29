import ipaddress
import logging
import random
import socket
import struct
from typing import Dict, Iterable, List, Optional, Tuple

import yaml


META_NAME_PREFIXES = ("剩余流量", "距离下次重置剩余", "套餐到期")


def _name_score(name: str) -> Tuple[int, str]:
    if any(name.startswith(prefix) for prefix in META_NAME_PREFIXES):
        return (3, name)
    if name.startswith("V-"):
        return (2, name)
    if name.startswith("S-"):
        return (1, name)
    return (0, name)


def _is_ip_address(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def _match_dns_policy(hostname: str, pattern: str) -> bool:
    if pattern.startswith("*."):
        return hostname.endswith(pattern[1:])
    return hostname == pattern


def _parse_dns_server(value: str) -> Optional[Tuple[str, int]]:
    if not isinstance(value, str):
        return None
    value = value.strip().strip("'").strip('"')
    if not value or "://" in value:
        return None
    if ":" not in value:
        return (value, 53)
    host, port = value.rsplit(":", 1)
    if not host:
        return None
    try:
        return (host, int(port))
    except ValueError:
        return None


def _dns_server_for_host(
    hostname: str, nameserver_policy: Dict[str, object]
) -> Optional[Tuple[str, int]]:
    for pattern, raw_value in nameserver_policy.items():
        if not _match_dns_policy(hostname, pattern):
            continue
        values = raw_value if isinstance(raw_value, list) else [raw_value]
        for value in values:
            server = _parse_dns_server(value)
            if server:
                return server
    return None


def _read_dns_name(packet: bytes, offset: int) -> Tuple[str, int]:
    labels = []
    jumped = False
    next_offset = offset

    while True:
        length = packet[offset]
        if length == 0:
            offset += 1
            if not jumped:
                next_offset = offset
            break
        if length & 0xC0 == 0xC0:
            current_offset = offset
            pointer = ((length & 0x3F) << 8) | packet[offset + 1]
            offset = pointer
            if not jumped:
                next_offset = current_offset + 2
                jumped = True
            continue

        offset += 1
        labels.append(packet[offset : offset + length].decode("ascii"))
        offset += length
        if not jumped:
            next_offset = offset

    return ".".join(labels), next_offset


def _resolve_a_record(hostname: str, dns_server: Tuple[str, int]) -> Optional[str]:
    dns_host, dns_port = dns_server
    tx_id = random.randint(0, 0xFFFF)
    header = struct.pack("!HHHHHH", tx_id, 0x0100, 1, 0, 0, 0)
    qname = b"".join(
        len(label).to_bytes(1, "big") + label.encode("idna")
        for label in hostname.rstrip(".").split(".")
    ) + b"\x00"
    question = qname + struct.pack("!HH", 1, 1)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(3)
        sock.sendto(header + question, (dns_host, dns_port))
        response, _ = sock.recvfrom(512)

    resp_tx_id, _, qd_count, an_count, _, _ = struct.unpack("!HHHHHH", response[:12])
    if resp_tx_id != tx_id:
        return None

    offset = 12
    for _ in range(qd_count):
        _, offset = _read_dns_name(response, offset)
        offset += 4

    for _ in range(an_count):
        _, offset = _read_dns_name(response, offset)
        record_type, record_class, _, rd_length = struct.unpack(
            "!HHIH", response[offset : offset + 10]
        )
        offset += 10
        record_data = response[offset : offset + rd_length]
        offset += rd_length
        if record_type == 1 and record_class == 1 and rd_length == 4:
            return socket.inet_ntoa(record_data)

    return None


def _resolve_server(hostname: str, nameserver_policy: Dict[str, object]) -> str:
    if _is_ip_address(hostname):
        return hostname

    dns_server = _dns_server_for_host(hostname, nameserver_policy)
    if not dns_server:
        return hostname

    resolved = _resolve_a_record(hostname, dns_server)
    if not resolved:
        logging.warning(
            "Failed to resolve %s using clash nameserver-policy %s:%s",
            hostname,
            dns_server[0],
            dns_server[1],
        )
        return hostname

    logging.info(
        "Resolved %s via clash nameserver-policy %s:%s -> %s",
        hostname,
        dns_server[0],
        dns_server[1],
        resolved,
    )
    return resolved


def _trojan_forward(proxy: Dict[str, object]) -> str:
    server = str(proxy["server"])
    password = str(proxy["password"])
    port = int(proxy["port"])
    name = str(proxy.get("name", ""))

    query_parts = []
    sni = proxy.get("sni")
    if sni:
        query_parts.append(f"serverName={sni}")
    if proxy.get("skip-cert-verify"):
        query_parts.append("skipVerify=true")

    result = f"forward=trojan://{password}@{server}:{port}"
    if query_parts:
        result = f"{result}?{'&'.join(query_parts)}"
    return f"{result}#{name}"


def _dedupe_key(proxy: Dict[str, object], resolved_server: str) -> Tuple[object, ...]:
    return (
        proxy.get("type"),
        resolved_server,
        proxy.get("port"),
        proxy.get("password"),
        proxy.get("sni") or "",
        bool(proxy.get("skip-cert-verify")),
        proxy.get("network") or "",
    )


def _supported_proxies(proxies: Iterable[Dict[str, object]]) -> Iterable[Dict[str, object]]:
    for proxy in proxies:
        if proxy.get("type") != "trojan":
            logging.info("Skipping clash proxy type '%s'", proxy.get("type"))
            continue
        if proxy.get("network") not in (None, "", "tcp"):
            logging.info(
                "Skipping clash trojan proxy '%s' with unsupported network '%s'",
                proxy.get("name"),
                proxy.get("network"),
            )
            continue
        yield proxy


def forwards_from_clash(path: str, backend: str) -> List[str]:
    if backend != "glider":
        raise NotImplementedError("Only glider backend is supported for clash.yaml input")

    with open(path, "r") as f:
        cfg = yaml.load(f, yaml.FullLoader) or {}

    nameserver_policy = cfg.get("dns", {}).get("nameserver-policy", {}) or {}
    selected: Dict[Tuple[object, ...], Dict[str, object]] = {}
    resolved_servers: Dict[str, str] = {}

    for proxy in _supported_proxies(cfg.get("proxies", []) or []):
        original_server = str(proxy["server"])
        if original_server not in resolved_servers:
            resolved_servers[original_server] = _resolve_server(
                original_server, nameserver_policy
            )
        resolved_server = resolved_servers[original_server]
        key = _dedupe_key(proxy, resolved_server)
        existing = selected.get(key)
        if existing is None or _name_score(str(proxy.get("name", ""))) < _name_score(
            str(existing.get("name", ""))
        ):
            selected[key] = {
                **proxy,
                "server": resolved_server,
            }

    return [_trojan_forward(proxy) for proxy in selected.values()]
