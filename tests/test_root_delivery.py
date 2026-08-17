from __future__ import annotations

from clear import root_delivery
from clear.tokens import encode_token_v3


def test_discover_clear_support_from_lightning_address(monkeypatch) -> None:
    def fake_get_json(url):
        assert url == "https://example.com/.well-known/nostr.json?name=alice"
        return {
            "names": {"alice": "11" * 32},
            "relays": {"11" * 32: ["wss://relay.example"]},
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
    assert discovery["recipient_pubkey"] == "11" * 32
    assert discovery["relays"] == ["wss://relay.example"]


def test_discover_clear_support_returns_unsupported_when_unit_differs(
    monkeypatch,
) -> None:
    def fake_get_json(url):
        return {
            "names": {"alice": "11" * 32},
            "relays": {"11" * 32: ["wss://relay.example"]},
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
                "pubkey": "22" * 32,
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
    assert discovery["recipient_pubkey"] == "22" * 32
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
