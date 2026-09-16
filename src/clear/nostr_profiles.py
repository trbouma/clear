"""Nostr profile lookup helpers for Clear public identities."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from stroma import KeyError as StromaKeyError
from stroma import Keys, RelayClient

DEFAULT_PROFILE_RELAYS = [
    "wss://relay.damus.io",
    "wss://nos.lol",
    "wss://relay.primal.net",
    "wss://relay.nostr.band",
]


class ProfileLookupError(Exception):
    """Raised when a Nostr profile lookup request is malformed."""


def _event_field(event, name: str):
    if isinstance(event, dict):
        return event.get(name)
    return getattr(event, name, None)


def _event_pubkey(event) -> str | None:
    return _event_field(event, "pub_key") or _event_field(event, "pubkey")


def _event_int(event, name: str, default: int = 0) -> int:
    value = _event_field(event, name)
    return value if isinstance(value, int) else default


def _event_data(event) -> dict:
    if isinstance(event, dict):
        return event
    data = event.data() if hasattr(event, "data") else {}
    return data if isinstance(data, dict) else {}


def normalize_profile_key(value: str) -> tuple[str, str]:
    """Return ``(pubkey_hex, npub)`` for an npub or hex public key."""

    try:
        pubkey = Keys(pub_k=value).public_key_hex()
        npub = Keys(pub_k=pubkey).public_key_bech32()
    except StromaKeyError as exc:
        raise ProfileLookupError(
            "profile lookup requires an npub or public key"
        ) from exc
    return pubkey, npub


async def lookup_nostr_profile(
    value: str,
    *,
    relays: Sequence[str] | None = None,
    timeout: float = 2.0,
    relay_client_type: type = RelayClient,
) -> dict[str, Any]:
    """Query public relays for the newest kind 0 metadata event for a key."""

    pubkey, npub = normalize_profile_key(value)
    selected_relays = list(relays or DEFAULT_PROFILE_RELAYS)
    errors: dict[str, str] = {}
    best_event = None
    for relay in selected_relays:
        try:
            client = relay_client_type(relay, timeout=timeout)
            events = await client.query(
                [{"authors": [pubkey], "kinds": [0], "limit": 1}]
            )
        except Exception as exc:
            errors[relay] = str(exc)
            continue
        for event in events:
            if _event_pubkey(event) != pubkey:
                continue
            if _event_int(event, "kind", -1) != 0:
                continue
            if (
                best_event is None
                or _event_int(event, "created_at")
                > _event_int(best_event, "created_at")
            ):
                best_event = event
    profile = None
    event_metadata = None
    if best_event is not None:
        content = _event_field(best_event, "content") or "{}"
        try:
            profile = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ProfileLookupError("profile metadata is not valid JSON") from exc
        if not isinstance(profile, dict):
            raise ProfileLookupError("profile metadata must be a JSON object")
        event_data = _event_data(best_event)
        event_metadata = {
            "id": event_data.get("id") or _event_field(best_event, "id"),
            "created_at": event_data.get("created_at")
            or _event_field(best_event, "created_at"),
        }
    return {
        "npub": npub,
        "pubkey": pubkey,
        "profile": profile,
        **({"event": event_metadata} if event_metadata else {}),
        "relays": selected_relays,
        **({"errors": errors} if errors else {}),
    }
