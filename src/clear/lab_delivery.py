"""Lab address discovery and token delivery helpers."""

from __future__ import annotations

import asyncio
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any

from clear.tokens import decode_token_v3

_BECH32_ALPHABET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
CLEAR_TRANSFER_KIND = 7379
CLEAR_TRANSFER_GIFT_WRAP_KIND = 1059
CLEAR_TRANSFER_PROTOCOL = "clear-token-transfer"


class DeliveryError(RuntimeError):
    pass


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


def _bech32_polymod(values: list[int]) -> int:
    generators = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]
    chk = 1
    for value in values:
        top = chk >> 25
        chk = (chk & 0x1FFFFFF) << 5 ^ value
        for index, generator in enumerate(generators):
            if (top >> index) & 1:
                chk ^= generator
    return chk


def _bech32_hrp_expand(hrp: str) -> list[int]:
    return [ord(char) >> 5 for char in hrp] + [0] + [ord(char) & 31 for char in hrp]


def _bech32_verify_checksum(hrp: str, data: list[int]) -> bool:
    return _bech32_polymod(_bech32_hrp_expand(hrp) + data) == 1


def _bech32_create_checksum(hrp: str, data: list[int]) -> list[int]:
    values = _bech32_hrp_expand(hrp) + data
    polymod = _bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ 1
    return [(polymod >> 5 * (5 - index)) & 31 for index in range(6)]


def _convert_bits(
    data: bytes | list[int],
    from_bits: int,
    to_bits: int,
    *,
    pad: bool,
) -> list[int]:
    accumulator = 0
    bits = 0
    result: list[int] = []
    max_value = (1 << to_bits) - 1
    max_accumulator = (1 << (from_bits + to_bits - 1)) - 1
    for value in data:
        if value < 0 or value >> from_bits:
            raise DeliveryError("invalid bech32 data")
        accumulator = ((accumulator << from_bits) | value) & max_accumulator
        bits += from_bits
        while bits >= to_bits:
            bits -= to_bits
            result.append((accumulator >> bits) & max_value)
    if pad:
        if bits:
            result.append((accumulator << (to_bits - bits)) & max_value)
    elif bits >= from_bits or ((accumulator << (to_bits - bits)) & max_value):
        raise DeliveryError("invalid bech32 padding")
    return result


def _bech32_decode(value: str) -> tuple[str, list[int]]:
    if value.lower() != value and value.upper() != value:
        raise DeliveryError("mixed-case bech32 string")
    value = value.lower()
    separator = value.rfind("1")
    if separator < 1 or separator + 7 > len(value):
        raise DeliveryError("invalid bech32 string")
    hrp = value[:separator]
    data = []
    for char in value[separator + 1 :]:
        index = _BECH32_ALPHABET.find(char)
        if index == -1:
            raise DeliveryError("invalid bech32 character")
        data.append(index)
    if not _bech32_verify_checksum(hrp, data):
        raise DeliveryError("invalid bech32 checksum")
    return hrp, data[:-6]


def _bech32_encode(hrp: str, data: list[int]) -> str:
    combined = data + _bech32_create_checksum(hrp, data)
    return hrp + "1" + "".join(_BECH32_ALPHABET[each] for each in combined)


def _npub_to_hex(value: str) -> str:
    value = value.strip()
    if value.startswith("npub"):
        hrp, data = _bech32_decode(value)
        if hrp != "npub":
            raise DeliveryError("recipient bech32 value is not an npub")
        decoded = bytes(_convert_bits(data, 5, 8, pad=False))
        if len(decoded) != 32:
            raise DeliveryError("npub does not contain a 32-byte public key")
        return decoded.hex()
    if len(value) == 64 and all(ch in "0123456789abcdefABCDEF" for ch in value):
        return value.lower()
    raise DeliveryError("recipient must resolve to an npub or 64-character pubkey")


def _pubkey_to_npub(pubkey: str) -> str:
    return _bech32_encode("npub", _convert_bits(bytes.fromhex(pubkey), 8, 5, pad=True))


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


def _nostr_modules():
    try:
        from monstr.client.client import ClientPool
        from monstr.encrypt import Keys
        from monstr.event.event import Event
        from monstr.signing.signing import BasicKeySigner
        from monstr.util import util_funcs
    except Exception as exc:  # pragma: no cover - depends on local nostr runtime
        raise DeliveryError(
            "Nostr delivery requires the monstr package and its native secp256k1 "
            "runtime. Run `poetry install` and ensure secp256k1 is available."
        ) from exc
    return ClientPool, Event, Keys, BasicKeySigner, util_funcs


class _KindGiftWrap:
    """Small NIP-59 gift-wrap helper that preserves the inner application kind."""

    def __init__(self, signer, *, kind_gift_wrap: int):
        self._signer = signer
        self._kind_gift_wrap = kind_gift_wrap

    @staticmethod
    def _created_ticks() -> int:
        _, _, _, _, util_funcs = _nostr_modules()
        return util_funcs.date_as_ticks(datetime.now())

    async def _make_rumour(self, evt):
        _, Event, _, _, _ = _nostr_modules()
        event_data = evt.data()
        event_data["sig"] = None
        event_data["pubkey"] = await self._signer.get_public_key()
        ret = Event.load(event_data)
        _ = ret.id
        return ret

    async def _make_seal(self, rumour_evt, to_pub_k: str):
        _, Event, _, _, _ = _nostr_modules()
        if rumour_evt.sig:
            raise DeliveryError("rumour event should not be signed")
        ret = Event(
            kind=Event.KIND_SEAL,
            content=await self._signer.nip44_encrypt(
                plain_text=json.dumps(rumour_evt.data()),
                to_pub_k=to_pub_k,
            ),
            created_at=self._created_ticks(),
            pub_key=await self._signer.get_public_key(),
            tags=[],
        )
        await self._signer.sign_event(ret)
        return ret

    async def wrap(self, evt, *, to_pub_k: str, expiration: int | None = None):
        _, Event, Keys, BasicKeySigner, _ = _nostr_modules()
        rumour_evt = await self._make_rumour(evt)
        sealed_evt = await self._make_seal(rumour_evt, to_pub_k)
        transient_key = Keys()
        transient_signer = BasicKeySigner(transient_key)
        tags = [["p", to_pub_k]]
        if expiration is not None:
            expiration = int(expiration)
            if expiration <= 0:
                raise DeliveryError("expiration must be a positive Unix timestamp")
            tags.append(["expiration", str(expiration)])
        ret = Event(
            kind=self._kind_gift_wrap,
            pub_key=transient_key.public_key_hex(),
            created_at=self._created_ticks(),
            content=await transient_signer.nip44_encrypt(
                plain_text=json.dumps(sealed_evt.data()),
                to_pub_k=to_pub_k,
            ),
            tags=tags,
        )
        await transient_signer.sign_event(ret)
        return ret, transient_key


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
        ClientPool, Event, Keys, BasicKeySigner, _ = _nostr_modules()
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
        wrapper = _KindGiftWrap(
            signer,
            kind_gift_wrap=CLEAR_TRANSFER_GIFT_WRAP_KIND,
        )
        event, transient_key = await wrapper.wrap(
            inner,
            to_pub_k=recipient_pubkey,
            expiration=expiration,
        )
        async with ClientPool(publish_relays) as client:
            client.publish(event)
            await asyncio.sleep(0.2)
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
            "expiration": expiration,
        }

    return {"delivery": discovery, "publish": asyncio.run(publish())}
