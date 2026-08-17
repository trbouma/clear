"""Cashu token serialization helpers."""

from __future__ import annotations

import base64
import json
from typing import Any


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
