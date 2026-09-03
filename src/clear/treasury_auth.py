"""Signed treasurer authorization envelopes backed by Stroma Nostr events."""

from __future__ import annotations

import json
import secrets
import time
from typing import Any

from stroma import Event, Keys
from stroma import KeyError as StromaKeyError

TREASURY_EVENT_KIND = 37379


class TreasuryAuthError(ValueError):
    pass


def npub_from_nsec(nsec: str) -> str:
    try:
        return Keys(priv_k=nsec).public_key_bech32()
    except StromaKeyError as exc:
        raise TreasuryAuthError(str(exc)) from exc


def npub_to_hex(npub: str) -> str:
    try:
        return Keys(pub_k=npub).public_key_hex()
    except StromaKeyError as exc:
        raise TreasuryAuthError(str(exc)) from exc


def canonical_payload(payload: dict[str, Any]) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sign_payload(payload: dict[str, Any], nsec: str) -> dict[str, Any]:
    try:
        event = Event(
            kind=TREASURY_EVENT_KIND,
            content=canonical_payload(payload),
            tags=[],
            created_at=int(payload.get("created_at") or time.time()),
        )
        event.sign(Keys(priv_k=nsec))
    except StromaKeyError as exc:
        raise TreasuryAuthError(str(exc)) from exc
    return event.data()


def build_cmu_create_envelope(
    *,
    mint: str,
    grant_id: str,
    name: str | None,
    nsec: str,
    unit_alias: str | None = None,
    lifetime_seconds: int = 300,
) -> dict[str, Any]:
    now = int(time.time())
    payload = {
        "action": "cmu:create",
        "grant_id": grant_id,
        "mint": mint.rstrip("/"),
        "name": name,
        "unit_alias": unit_alias,
        "nonce": secrets.token_hex(32),
        "created_at": now,
        "expires_at": now + lifetime_seconds,
    }
    return {"payload": payload, "event": sign_payload(payload, nsec)}


def build_cmu_info_envelope(
    *,
    mint: str,
    nsec: str,
    lifetime_seconds: int = 300,
) -> dict[str, Any]:
    now = int(time.time())
    payload = {
        "action": "cmu:info",
        "mint": mint.rstrip("/"),
        "nonce": secrets.token_hex(32),
        "created_at": now,
        "expires_at": now + lifetime_seconds,
    }
    return {"payload": payload, "event": sign_payload(payload, nsec)}


def build_quote_authorize_envelope(
    *,
    mint: str,
    quote_id: str,
    nsec: str,
    lifetime_seconds: int = 300,
) -> dict[str, Any]:
    now = int(time.time())
    payload = {
        "action": "quote:authorize",
        "mint": mint.rstrip("/"),
        "quote_id": quote_id,
        "nonce": secrets.token_hex(32),
        "created_at": now,
        "expires_at": now + lifetime_seconds,
    }
    return {"payload": payload, "event": sign_payload(payload, nsec)}


def verify_envelope(
    envelope: dict[str, Any],
    *,
    expected_action: str,
    expected_mint: str,
    now: int | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = envelope.get("payload")
    event_data = envelope.get("event")
    if not isinstance(payload, dict) or not isinstance(event_data, dict):
        raise TreasuryAuthError("treasury request must include payload and event")
    if payload.get("action") != expected_action:
        raise TreasuryAuthError("treasury action does not match endpoint")
    if payload.get("mint") != expected_mint.rstrip("/"):
        raise TreasuryAuthError("treasury request is for a different mint")
    nonce = payload.get("nonce")
    if not isinstance(nonce, str) or len(nonce) < 32:
        raise TreasuryAuthError("treasury request nonce is missing or too short")
    created_at = payload.get("created_at")
    expires_at = payload.get("expires_at")
    if not isinstance(created_at, int) or not isinstance(expires_at, int):
        raise TreasuryAuthError("treasury request timestamps must be integers")
    current = int(time.time()) if now is None else now
    if created_at > current + 60:
        raise TreasuryAuthError("treasury request is from the future")
    if expires_at < current:
        raise TreasuryAuthError("treasury request has expired")
    event = Event.load(event_data, validate=True)
    if event is None:
        raise TreasuryAuthError("treasury event signature is invalid")
    if event.kind != TREASURY_EVENT_KIND:
        raise TreasuryAuthError("treasury event kind is not supported")
    if event.content != canonical_payload(payload):
        raise TreasuryAuthError("treasury event content does not match payload")
    return payload, event.data()
