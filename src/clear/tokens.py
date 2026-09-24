"""Cashu token serialization helpers."""

from __future__ import annotations

import base64
import json
import re
from collections.abc import Callable
from io import BytesIO
from typing import Any

import cbor2


def _base64_urlsafe(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def encode_token_v3(
    *,
    mint: str,
    proofs: list[dict[str, Any]],
    unit: str,
    memo: str | None = None,
) -> str:
    """Encode proofs as a Cashu TokenV3 string.

    TokenV3 is the JSON-based Cashu token format with the ``cashuA`` prefix.
    """

    payload: dict[str, Any] = {
        "token": [{"mint": mint.rstrip("/"), "proofs": proofs}],
        "unit": unit,
    }
    if memo:
        payload["memo"] = memo
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return f"cashuA{_base64_urlsafe(serialized)}"


def decode_token_v3(token: str) -> dict[str, Any]:
    if token.startswith("cashu:"):
        token = token.removeprefix("cashu:")
    if not token.startswith("cashuA"):
        raise ValueError("expected a Cashu TokenV3 string with cashuA prefix")
    encoded = token.removeprefix("cashuA")
    padding = "=" * (-len(encoded) % 4)
    decoded = base64.urlsafe_b64decode(encoded + padding)
    payload = json.loads(decoded)
    if not isinstance(payload, dict):
        raise ValueError("decoded token payload must be an object")
    return payload


# Bound untrusted input before Base64/CBOR allocation. HTTP transports may set
# smaller limits; this also accommodates tokens exchanged outside HTTP.
MAX_TOKEN_LENGTH = 1_000_000
KeysetResolver = Callable[[str, str], str]


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _binary(value: Any, name: str, lengths: tuple[int, ...]) -> bytes:
    if not isinstance(value, bytes) or len(value) not in lengths:
        raise ValueError(f"invalid {name} bytes")
    return value


def _hex_bytes(value: Any, name: str, lengths: tuple[int, ...]) -> bytes:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-fA-F]+", value):
        raise ValueError(f"{name} must be hexadecimal")
    try:
        return _binary(bytes.fromhex(value), name, lengths)
    except ValueError as exc:
        raise ValueError(f"invalid {name}") from exc


def _amount(value: Any) -> int:
    if type(value) is not int or not 0 < value < 2**64:
        raise ValueError("proof amount must be a positive uint64")
    return value


def encode_token_v4(
    *,
    mint: str,
    proofs: list[dict[str, Any]],
    unit: str,
    memo: str | None = None,
) -> str:
    """Encode NUT-00 TokenV4, retaining full keyset IDs and custom units."""
    if not proofs:
        raise ValueError("token must include at least one proof")
    groups: dict[bytes, list[dict[str, Any]]] = {}
    for proof in proofs:
        keyset = _hex_bytes(proof["id"], "keyset ID", (8, 33))
        if len(keyset) == 8 and keyset[0] != 0:
            raise ValueError("encoding requires a full keyset ID")
        item = {
            "a": _amount(proof["amount"]),
            "s": _text(proof["secret"], "secret"),
            "c": _hex_bytes(proof["C"], "signature", (33,)),
        }
        if "dleq" in proof:
            item["d"] = {
                field: _hex_bytes(proof["dleq"][field], "DLEQ scalar", (32,))
                for field in ("e", "s", "r")
            }
        if "witness" in proof:
            item["w"] = _text(proof["witness"], "witness")
        groups.setdefault(keyset, []).append(item)
    payload = {
        "m": _text(mint.rstrip("/"), "mint"),
        "u": _text(unit, "unit"),
        "t": [{"i": keyset, "p": items} for keyset, items in groups.items()],
    }
    if memo is not None:
        if not isinstance(memo, str):
            raise ValueError("memo must be a string")
        payload["d"] = memo
    token = "cashuB" + _base64_urlsafe(cbor2.dumps(payload))
    if len(token) > MAX_TOKEN_LENGTH:
        raise ValueError("token exceeds size limit")
    return token


def decode_token_v4(
    token: str,
    *,
    resolve_keyset: KeysetResolver | None = None,
) -> dict[str, Any]:
    """Decode into the same proof envelope as V3, without verifying signatures.

    Abbreviated modern IDs require an explicit trusted-mint resolver. Legacy
    00 IDs are already complete at eight bytes. No network I/O occurs here.
    """
    token = token.removeprefix("cashu:")
    if len(token) > MAX_TOKEN_LENGTH:
        raise ValueError("token exceeds size limit")
    if not token.startswith("cashuB"):
        raise ValueError("expected a Cashu TokenV4 string with cashuB prefix")
    encoded = token[6:]
    if not re.fullmatch(r"[A-Za-z0-9_-]+={0,2}", encoded):
        raise ValueError("invalid token Base64URL")
    try:
        raw = base64.b64decode(
            encoded + "=" * (-len(encoded) % 4),
            altchars=b"-_",
            validate=True,
        )
        stream = BytesIO(raw)
        payload = cbor2.CBORDecoder(stream).decode()
        if stream.read(1):
            raise ValueError("trailing data after token")
        if not isinstance(payload, dict):
            raise ValueError("token must be a CBOR map")
        mint = _text(payload["m"], "mint").rstrip("/")
        _text(mint, "mint")
        unit = _text(payload["u"], "unit")
        groups = payload["t"]
        if not isinstance(groups, list) or not groups:
            raise ValueError("token must include keyset groups")
        proofs = []
        for group in groups:
            keyset = _binary(group["i"], "keyset ID", (8, 33)).hex()
            if len(keyset) == 16 and not keyset.startswith("00"):
                if resolve_keyset is None:
                    raise ValueError("short keyset ID requires mint keyset resolution")
                full_id = resolve_keyset(mint, keyset)
                _hex_bytes(full_id, "resolved keyset ID", (33,))
                if not full_id.startswith(keyset):
                    raise ValueError("resolved keyset ID does not match short ID")
                keyset = full_id
            if not isinstance(group["p"], list) or not group["p"]:
                raise ValueError("keyset group must include proofs")
            for item in group["p"]:
                proof = {
                    "id": keyset,
                    "amount": _amount(item["a"]),
                    "secret": _text(item["s"], "secret"),
                    "C": _binary(item["c"], "signature", (33,)).hex(),
                }
                if "d" in item:
                    proof["dleq"] = {
                        field: _binary(item["d"][field], "DLEQ scalar", (32,)).hex()
                        for field in ("e", "s", "r")
                    }
                if "w" in item:
                    proof["witness"] = _text(item["w"], "witness")
                proofs.append(proof)
        result = {"token": [{"mint": mint, "proofs": proofs}], "unit": unit}
        if "d" in payload:
            if not isinstance(payload["d"], str):
                raise ValueError("memo must be a string")
            result["memo"] = payload["d"]
        return result
    except (
        KeyError,
        TypeError,
        ValueError,
        cbor2.CBORDecodeError,
        RecursionError,
        OverflowError,
    ) as exc:
        # Do not include bearer secrets or raw input in error messages.
        raise ValueError("invalid cashuB token or unresolved keyset ID") from exc


def decode_token(
    token: str,
    *,
    resolve_keyset: KeysetResolver | None = None,
) -> dict[str, Any]:
    """Accept either Cashu wire format, optionally prefixed with cashu:."""
    token = token.strip()
    if len(token) > MAX_TOKEN_LENGTH:
        raise ValueError("token exceeds size limit")
    if token.removeprefix("cashu:").startswith("cashuB"):
        return decode_token_v4(token, resolve_keyset=resolve_keyset)
    return decode_token_v3(token)
