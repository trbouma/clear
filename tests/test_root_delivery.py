from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from stroma import Keys

from clear import root_delivery
from clear.tokens import encode_token_v3

RECIPIENT = Keys(priv_k="1".zfill(64))
RECIPIENT_PUBKEY = RECIPIENT.public_key_hex()
RECIPIENT_NPUB = RECIPIENT.public_key_bech32()
SECOND_RECIPIENT = Keys(priv_k="2".zfill(64))
SECOND_RECIPIENT_PUBKEY = SECOND_RECIPIENT.public_key_hex()


def test_discover_clear_support_from_lightning_address(monkeypatch) -> None:
    def fake_get_json(url):
        assert url == "https://example.com/.well-known/nostr.json?name=alice"
        return {
            "names": {"alice": RECIPIENT_PUBKEY},
            "relays": {RECIPIENT_PUBKEY: ["wss://relay.example"]},
            "clear": {
                "mints": ["http://clear.example"],
                "units": ["cmu-0011223344556677"],
                "protocols": ["clear-token-transfer"],
                "transports": ["nip59"],
                "kinds": [7379],
                "label": "Alice Clear Wallet",
            },
        }

    monkeypatch.setattr(root_delivery, "_get_json", fake_get_json)

    discovery = root_delivery.discover_clear_support(
        "alice@example.com",
        mint_url="http://clear.example",
        unit="cmu-0011223344556677",
    )

    assert discovery["supported"] is True
    assert discovery["source"] == "nip05"
    assert discovery["recipient_pubkey"] == RECIPIENT_PUBKEY
    assert discovery["relays"] == ["wss://relay.example"]


def test_discover_clear_support_returns_unsupported_when_unit_differs(
    monkeypatch,
) -> None:
    def fake_get_json(url):
        return {
            "names": {"alice": RECIPIENT_PUBKEY},
            "relays": {RECIPIENT_PUBKEY: ["wss://relay.example"]},
            "clear": {
                "mints": ["http://clear.example"],
                "units": ["cmu-other"],
                "protocols": ["clear-token-transfer"],
                "transports": ["nip59"],
                "kinds": [7379],
            }
        }

    monkeypatch.setattr(root_delivery, "_get_json", fake_get_json)

    discovery = root_delivery.discover_clear_support(
        "alice@example.com",
        mint_url="http://clear.example",
        unit="cmu-0011223344556677",
    )

    assert discovery["supported"] is False


def test_discover_clear_support_from_lightning_address_descriptor(
    monkeypatch,
) -> None:
    def fake_get_json(url):
        if url == "https://example.com/.well-known/nostr.json?name=alice":
            raise root_delivery.DeliveryError("no nostr.json")
        assert url == "https://example.com/.well-known/lnurlp/alice"
        return {
            "callback": "https://example.com/lnurl",
            "clear": {
                "pubkey": SECOND_RECIPIENT_PUBKEY,
                "relays": ["wss://relay.example"],
                "mints": ["http://clear.example"],
                "units": ["cmu-0011223344556677"],
                "protocols": ["clear-token-transfer"],
                "transports": ["nip59"],
                "kinds": [7379],
            },
        }

    monkeypatch.setattr(root_delivery, "_get_json", fake_get_json)

    discovery = root_delivery.discover_clear_support(
        "alice@example.com",
        mint_url="http://clear.example",
        unit="cmu-0011223344556677",
    )

    assert discovery["supported"] is True
    assert discovery["source"] == "lightning-address"
    assert discovery["recipient_pubkey"] == SECOND_RECIPIENT_PUBKEY
    assert discovery["relays"] == ["wss://relay.example"]


def test_keyset_ids_from_token_are_sorted_unique() -> None:
    token = encode_token_v3(
        mint="http://clear.example",
        unit="cmu-0011223344556677",
        proofs=[
            {"amount": 4, "id": "keyset-b", "secret": "a", "C": "b"},
            {"amount": 1, "id": "keyset-a", "secret": "c", "C": "d"},
            {"amount": 1, "id": "keyset-b", "secret": "e", "C": "f"},
        ],
    )

    assert root_delivery._keyset_ids_from_token(token) == ["keyset-a", "keyset-b"]


def test_publish_verified_retries_until_relay_returns_event(monkeypatch) -> None:
    event = SimpleNamespace(id="event-id", kind=1059)

    class FakePool:
        publishes = 0
        queries = 0

        def __init__(self, relays):
            assert relays == ["wss://relay.example"]

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        def publish(self, candidate):
            assert candidate is event
            self.__class__.publishes += 1

        async def query(self, filters):
            assert filters[0]["ids"] == ["event-id"]
            self.__class__.queries += 1
            return [event] if self.queries == 2 else []

    monkeypatch.setattr(root_delivery.asyncio, "sleep", AsyncMock())

    verified = root_delivery.asyncio.run(
        root_delivery._publish_verified(
            FakePool,
            event,
            ["wss://relay.example"],
        )
    )

    assert verified == ["wss://relay.example"]
    assert FakePool.publishes == 2
    assert FakePool.queries == 2


def test_publish_verified_fails_when_relay_query_fails(monkeypatch) -> None:
    event = SimpleNamespace(id="missing-event", kind=1059)

    class FailingPool:
        def __init__(self, relays):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        def publish(self, candidate):
            pass

        async def query(self, filters):
            raise RuntimeError("relay unavailable")

    monkeypatch.setattr(root_delivery.asyncio, "sleep", AsyncMock())

    with pytest.raises(root_delivery.DeliveryError, match="could not be verified"):
        root_delivery.asyncio.run(
            root_delivery._publish_verified(
                FailingPool,
                event,
                ["wss://relay.example"],
            )
        )
