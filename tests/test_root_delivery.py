from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from stroma import Keys

from clear import root_delivery
from clear.tokens import encode_token_v3, encode_token_v4

RECIPIENT = Keys(priv_k="1".zfill(64))
RECIPIENT_PUBKEY = RECIPIENT.public_key_hex()
RECIPIENT_NPUB = RECIPIENT.public_key_bech32()
SECOND_RECIPIENT = Keys(priv_k="2".zfill(64))
SECOND_RECIPIENT_PUBKEY = SECOND_RECIPIENT.public_key_hex()


def test_mint_public_route_requires_well_formed_https() -> None:
    assert root_delivery.mint_has_public_route("https://clear.example") is True
    assert root_delivery.mint_has_public_route("https://clear.example/path/") is True
    assert root_delivery.mint_has_public_route("http://clear:3339") is False
    assert root_delivery.mint_has_public_route("https://user@clear.example") is False
    assert root_delivery.mint_has_public_route("https://clear.example?q=1") is False


def test_explicit_wallet_keys_still_work():
    for key in (RECIPIENT_NPUB, RECIPIENT_PUBKEY):
        result = root_delivery.discover_clear_support(
            key, mint_url="https://mint.example", unit="credits")
        assert result["recipient_pubkey"] == RECIPIENT_PUBKEY
        assert result["source"] == "pubkey" and result["supported"]
        assert result["relays"] == []


@pytest.mark.parametrize("encoder", [encode_token_v3, encode_token_v4])
def test_keyset_ids_from_token_are_sorted_unique(encoder) -> None:
    token = encoder(
        mint="http://clear.example",
        unit="cmu-0011223344556677",
        proofs=[
            {"amount": 4, "id": "0022222222222222",
             "secret": "a", "C": "02" + "11" * 32},
            {"amount": 1, "id": "0011111111111111",
             "secret": "c", "C": "02" + "11" * 32},
            {"amount": 1, "id": "0022222222222222",
             "secret": "e", "C": "02" + "11" * 32},
        ],
    )

    assert root_delivery._keyset_ids_from_token(token) == [
        "0011111111111111", "0022222222222222",
    ]


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
