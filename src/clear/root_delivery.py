"""Clear address discovery and token delivery helpers."""

from __future__ import annotations

import asyncio
import inspect
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from stroma import BasicKeySigner, Event, GiftWrap, Keys, RelayClient
from stroma import KeyError as StromaKeyError

from clear.tokens import decode_token_v3

CLEAR_TRANSFER_KIND = 7379
CLEAR_TRANSFER_GIFT_WRAP_KIND = 1059
CLEAR_TRANSFER_PROTOCOL = "clear-token-transfer"
DELIVERY_VERIFY_TIMEOUT_SECONDS = 10.0


class DeliveryError(RuntimeError):
    pass


class _RelaySession:
    def __init__(
        self,
        relays: list[str],
        *,
        timeout: float = DELIVERY_VERIFY_TIMEOUT_SECONDS,
    ):
        if len(relays) != 1:
            raise DeliveryError("relay verification expects one relay per session")
        self._client = RelayClient(
            relays[0],
            timeout=timeout,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def publish(self, event) -> None:
        await self._client.publish(event)

    async def query(self, filters):
        return await self._client.query(filters)


async def _publish_verified(
    client_pool_type,
    event,
    relays: list[str],
    *,
    timeout: float = DELIVERY_VERIFY_TIMEOUT_SECONDS,
) -> list[str]:
    """Publish until at least one recipient relay returns the exact event."""

    event_id = str(event.id)
    verified_relays: list[str] = []
    errors: dict[str, str] = {}
    for relay in relays:
        deadline = asyncio.get_running_loop().time() + max(0.5, float(timeout))
        try:
            try:
                client_pool = client_pool_type([relay], timeout=timeout)
            except TypeError:
                client_pool = client_pool_type([relay])
            async with client_pool as client:
                while asyncio.get_running_loop().time() < deadline:
                    published = client.publish(event)
                    if inspect.isawaitable(published):
                        await published
                    await asyncio.sleep(0.4)
                    observed = await client.query(
                        [{
                            "ids": [event_id],
                            "kinds": [int(event.kind)],
                            "limit": 1,
                        }]
                    )
                    if any(str(candidate.id) == event_id for candidate in observed):
                        verified_relays.append(relay)
                        break
        except Exception as exc:
            errors[relay] = str(exc)

    if not verified_relays:
        detail = "; ".join(
            f"{relay}: {message}" for relay, message in errors.items()
        )
        suffix = f" ({detail})" if detail else ""
        raise DeliveryError(
            f"relay delivery could not be verified for event {event_id}{suffix}"
        )
    return verified_relays


def _get_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        raise DeliveryError(f"GET {url} failed with {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise DeliveryError(f"GET {url} failed: {exc.reason}") from exc
    if not isinstance(payload, dict):
        raise DeliveryError(f"GET {url} did not return a JSON object")
    return payload


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise DeliveryError(f"POST {url} failed with {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise DeliveryError(f"POST {url} failed: {exc.reason}") from exc
    return json.loads(body) if body else {"status": "OK"}


def _address_parts(address: str) -> tuple[str, str]:
    local, sep, domain = address.strip().lower().partition("@")
    if not sep or not local or not domain:
        raise DeliveryError("address must be a lightning address or NIP-05 name")
    return local, domain


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.rstrip("/")]
    if isinstance(value, list):
        return [str(each).rstrip("/") for each in value]
    return []


def _npub_to_hex(value: str) -> str:
    try:
        return Keys(pub_k=value.strip()).public_key_hex()
    except StromaKeyError as exc:
        raise DeliveryError(
            "recipient must resolve to an npub or 64-character pubkey"
        ) from exc


def _pubkey_to_npub(pubkey: str) -> str:
    try:
        return Keys(pub_k=pubkey).public_key_bech32()
    except StromaKeyError as exc:
        raise DeliveryError("recipient public key is invalid") from exc


def _descriptor_from_payload(
    payload: dict[str, Any],
    local: str,
) -> dict[str, Any] | None:
    candidate = (
        payload.get("clear")
        or payload.get("clear_mint")
        or payload.get("clearMint")
    )
    if (
        isinstance(candidate, dict)
        and local in candidate
        and isinstance(candidate[local], dict)
    ):
        return candidate[local]
    if isinstance(candidate, dict):
        return candidate
    return None


def _match_descriptor(
    descriptor: dict[str, Any],
    *,
    mint_url: str,
    unit: str,
) -> dict[str, Any] | None:
    mints = _as_list(descriptor.get("mints") or descriptor.get("mint"))
    units = _as_list(descriptor.get("units") or descriptor.get("unit"))
    normalized_mint = mint_url.rstrip("/")
    if mints and normalized_mint not in mints:
        return None
    if units and unit not in units:
        return None
    protocols = _as_list(descriptor.get("protocols") or descriptor.get("protocol"))
    transports = _as_list(descriptor.get("transports") or descriptor.get("transport"))
    try:
        kinds = [int(each) for each in descriptor.get("kinds", []) or []]
    except (TypeError, ValueError):
        return None
    if protocols and CLEAR_TRANSFER_PROTOCOL not in protocols:
        return None
    if transports and "nip59" not in transports and "gift-wrap" not in transports:
        return None
    if kinds and CLEAR_TRANSFER_KIND not in kinds:
        return None
    recipient_pubkey = descriptor.get("pubkey") or descriptor.get("npub")
    if isinstance(recipient_pubkey, str):
        try:
            recipient_pubkey = _npub_to_hex(recipient_pubkey)
        except DeliveryError:
            return None
    else:
        recipient_pubkey = None
    return {
        "mints": mints,
        "units": units,
        "protocols": protocols,
        "transports": transports,
        "kinds": kinds,
        "label": descriptor.get("label"),
        **(
            {
                "recipient_pubkey": recipient_pubkey,
                "recipient_npub": _pubkey_to_npub(recipient_pubkey),
            }
            if recipient_pubkey
            else {}
        ),
        **(
            {"relays": _as_list(descriptor.get("relays"))}
            if descriptor.get("relays")
            else {}
        ),
    }


def _nip05_discovery(
    address: str,
    *,
    mint_url: str,
    unit: str,
) -> dict[str, Any]:
    local, domain = _address_parts(address)
    url = f"https://{domain}/.well-known/nostr.json?name={urllib.parse.quote(local)}"
    payload = _get_json(url)
    names = payload.get("names")
    relays = payload.get("relays") or {}
    if not isinstance(names, dict):
        raise DeliveryError("NIP-05 response is missing names")
    pubkey = names.get(local) or names.get(local.lower())
    if not isinstance(pubkey, str):
        raise DeliveryError("NIP-05 response does not name this address")
    pubkey = _npub_to_hex(pubkey)
    recipient_relays = _as_list(
        relays.get(pubkey) or relays.get(pubkey.lower())
        if isinstance(relays, dict)
        else None
    )
    descriptor = _descriptor_from_payload(payload, local)
    match = (
        _match_descriptor(descriptor, mint_url=mint_url, unit=unit)
        if descriptor is not None
        else None
    )
    return {
        "address": address,
        "supported": match is not None,
        "source": "nip05",
        "lookup_url": url,
        "mint": mint_url.rstrip("/"),
        "unit": unit,
        "recipient_pubkey": pubkey,
        "recipient_npub": _pubkey_to_npub(pubkey),
        "relays": recipient_relays,
        **(match or {}),
    }


def discover_clear_support(address: str, *, mint_url: str, unit: str) -> dict[str, Any]:
    if "@" not in address:
        pubkey = _npub_to_hex(address.strip())
        return {
            "address": address,
            "supported": True,
            "source": "pubkey",
            "mint": mint_url.rstrip("/"),
            "unit": unit,
            "recipient_pubkey": pubkey,
            "recipient_npub": _pubkey_to_npub(pubkey),
            "relays": [],
        }

    errors: list[str] = []
    try:
        return _nip05_discovery(address, mint_url=mint_url, unit=unit)
    except DeliveryError as exc:
        errors.append(str(exc))

    local, domain = _address_parts(address)
    checks = [
        (
            "lightning-address",
            f"https://{domain}/.well-known/lnurlp/{urllib.parse.quote(local)}",
        ),
    ]
    for kind, url in checks:
        try:
            payload = _get_json(url)
        except DeliveryError as exc:
            errors.append(str(exc))
            continue
        descriptor = _descriptor_from_payload(payload, local)
        if descriptor is None:
            continue
        match = _match_descriptor(descriptor, mint_url=mint_url, unit=unit)
        if match is not None:
            return {
                "address": address,
                "supported": True,
                "source": kind,
                "lookup_url": url,
                "mint": mint_url.rstrip("/"),
                "unit": unit,
                **match,
            }
    return {
        "address": address,
        "supported": False,
        "mint": mint_url.rstrip("/"),
        "unit": unit,
        "errors": errors,
    }


def _keyset_ids_from_token(token: str) -> list[str]:
    decoded = decode_token_v3(token)
    keyset_ids: set[str] = set()
    for token_entry in decoded.get("token", []):
        if not isinstance(token_entry, dict):
            continue
        for proof in token_entry.get("proofs", []):
            if isinstance(proof, dict) and proof.get("id"):
                keyset_ids.add(str(proof["id"]))
    return sorted(keyset_ids)


def deliver_clear_token(
    discovery: dict[str, Any],
    *,
    token: str,
    amount: int,
    sender_secret: str | None = None,
    memo: str | None = None,
    relays: list[str] | None = None,
    expiration: int | None = None,
) -> dict[str, Any]:
    if not discovery.get("supported"):
        raise DeliveryError("address does not advertise compatible Clear support")
    recipient_pubkey = discovery.get("recipient_pubkey")
    if not isinstance(recipient_pubkey, str):
        raise DeliveryError("discovery did not resolve a recipient pubkey")
    publish_relays = _as_list(relays) or _as_list(discovery.get("relays"))
    if not publish_relays:
        raise DeliveryError("no recipient relay available for Clear delivery")
    payload = {
        "type": "clear-token",
        "version": 1,
        "token": token,
        "mint": discovery["mint"],
        "unit": discovery["unit"],
        "amount": amount,
        "keyset_ids": _keyset_ids_from_token(token),
        "memo": memo,
    }

    async def publish() -> dict[str, Any]:
        sender_key = Keys(priv_k=sender_secret) if sender_secret else Keys()
        sender_pubkey = sender_key.public_key_hex()
        signer = BasicKeySigner(sender_key)
        inner = Event(
            kind=CLEAR_TRANSFER_KIND,
            content=json.dumps(payload),
            pub_key=sender_pubkey,
            tags=[
                ["p", recipient_pubkey],
                ["protocol", CLEAR_TRANSFER_PROTOCOL],
                ["v", "1"],
            ],
        )
        wrapper = GiftWrap(
            signer,
            gift_wrap_kind=CLEAR_TRANSFER_GIFT_WRAP_KIND,
        )
        event, transient_key = await wrapper.wrap(
            inner,
            recipient_pubkey,
            expiration=expiration,
        )
        verified_relays = await _publish_verified(
            _RelaySession,
            event,
            publish_relays,
        )
        return {
            "status": "OK",
            "event_id": event.id,
            "kind": event.kind,
            "transfer_kind": CLEAR_TRANSFER_KIND,
            "gift_wrap_kind": CLEAR_TRANSFER_GIFT_WRAP_KIND,
            "protocol": CLEAR_TRANSFER_PROTOCOL,
            "recipient_pubkey": recipient_pubkey,
            "recipient_npub": discovery.get("recipient_npub"),
            "sender_pubkey": sender_pubkey,
            "sender_ephemeral": sender_secret is None,
            "transient_pubkey": transient_key.public_key_hex(),
            "relays": publish_relays,
            "verified_relays": verified_relays,
            "verified": True,
            "expiration": expiration,
        }

    return {"delivery": discovery, "publish": asyncio.run(publish())}
