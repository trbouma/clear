"""Public-only Safebox v1 Clear discovery; never consult social NIP-05.

Implements the same wire contract as acorn.safebox_discovery without importing
Acorn's custody/wallet stack into the independent treasury CLI.
"""

from __future__ import annotations

import http.client
import ipaddress
import json
import re
import socket
import ssl
from urllib.parse import urlsplit

from stroma import Keys

MAX_BYTES = 65536


def normalize_address(address: str) -> str:
    if address.count("@") != 1:
        raise ValueError("Invalid wallet address")
    name, domain = address.strip().lower().split("@")
    domain = domain.encode("idna").decode("ascii")
    if not re.fullmatch(r"[a-z0-9_.-]{1,64}", name):
        raise ValueError("Invalid wallet name")
    public_host(domain)
    return f"{name}@{domain}"


def public_host(host: str) -> None:
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        if (
            len(host) > 253
            or "." not in host
            or host.endswith(
                (".localhost", ".local", ".lan", ".internal", ".home.arpa")
            )
            or any(
                not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", p)
                for p in host.split(".")
            )
        ):
            raise ValueError("Public hostname required") from None
    else:
        if not ip.is_global or ip.is_multicast:
            raise ValueError("Public address required")


def unique_object(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("Duplicate JSON member")
        result[name] = value
    return result


def fetch_directory(address: str) -> dict:
    name, host = address.split("@")
    addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    ips = list(dict.fromkeys(row[4][0] for row in addresses))
    if not ips:
        raise ValueError("Wallet host unavailable")
    for ip in ips:
        public_host(ip)

    class PinnedHTTPS(http.client.HTTPSConnection):
        def connect(self):
            sock = socket.create_connection((ips[0], 443), timeout=10)
            try:
                self.sock = ssl.create_default_context().wrap_socket(
                    sock, server_hostname=host
                )
            except BaseException:
                sock.close()
                raise

    connection = PinnedHTTPS(host, timeout=10)
    try:
        connection.request(
            "GET",
            f"/.well-known/safebox.json?name={name}",
            headers={"Accept": "application/json"},
        )
        response = connection.getresponse()
        if response.status != 200:
            raise ValueError("Wallet directory unavailable")
        body = response.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            raise ValueError("Wallet directory too large")
        return json.loads(body, object_pairs_hook=unique_object)
    except http.client.HTTPException as exc:
        raise ValueError("Invalid wallet directory response") from exc
    finally:
        connection.close()


def parse_directory(payload, address: str, unit: str) -> dict:
    if (
        not isinstance(payload, dict)
        or type(payload.get("version")) is not int
        or payload["version"] != 1
        or payload.get("address") != address
    ):
        raise ValueError("Invalid wallet directory version or address")
    key = payload.get("pubkey")
    if not isinstance(key, str) or not re.fullmatch(r"[0-9a-f]{64}", key):
        raise ValueError("Invalid wallet key")
    Keys(pub_k=key)
    relays = payload.get("relays")
    if not isinstance(relays, list) or not 1 <= len(relays) <= 8:
        raise ValueError("Wallet relay list required")
    for relay in relays:
        if (
            not isinstance(relay, str)
            or len(relay) > 2048
            or "\\" in relay
            or any(c.isspace() or ord(c) < 32 for c in relay)
        ):
            raise ValueError("Invalid wallet relay")
        parsed = urlsplit(relay)
        if (
            parsed.scheme != "wss"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.fragment
            or (parsed.port is not None and not 1 <= parsed.port <= 65535)
        ):
            raise ValueError("Invalid wallet relay")
        public_host(parsed.hostname)
    if len(set(relays)) != len(relays):
        raise ValueError("Duplicate wallet relay")
    caps = payload.get("capabilities")
    if not isinstance(caps, dict) or not caps:
        raise ValueError("Wallet capabilities required")
    supported = False
    if "clear-token-transfer" in caps:
        cap = caps["clear-token-transfer"]
        if not isinstance(cap, dict):
            raise ValueError("Invalid Clear capability")
        transports, kinds = cap.get("transports"), cap.get("kinds")
        if (
            not isinstance(transports, list)
            or "nip59" not in transports
            or any(not isinstance(t, str) for t in transports)
            or not isinstance(kinds, list)
            or 7379 not in kinds
            or any(type(k) is not int for k in kinds)
        ):
            raise ValueError("Invalid Clear transport")
        units = cap.get("units")
        if "units" in cap and (
            not isinstance(units, list)
            or not units
            or any(not isinstance(u, str) or not u or len(u) > 128 for u in units)
        ):
            raise ValueError("Invalid Clear units")
        supported = units is None or unit in units
    # Extensions cannot override the wallet key/relays or introduce mint policy.
    return {
        "address": address,
        "supported": supported,
        "recipient_pubkey": key,
        "relays": list(relays),
    }


def discover_wallet(address: str, unit: str) -> dict:
    address = normalize_address(address)
    return parse_directory(fetch_directory(address), address, unit)
