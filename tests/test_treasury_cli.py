from __future__ import annotations

import argparse
import json

import pytest
from stroma import Event, Keys

from clear import treasury_cli
from clear.root_wallet import deposit_issue, load_wallet
from clear.tokens import decode_token_v3
from clear.treasury_auth import TREASURY_EVENT_KIND


def test_treasury_cli_cmu_create_signs_and_posts_envelope(monkeypatch, capsys) -> None:
    calls = []
    treasurer = Keys(priv_k="1".zfill(64))

    def fake_request_json(mint_url, method, path, payload=None, *, token=None):
        calls.append((mint_url, method, path, payload, token))
        event = Event.load(payload["event"], validate=True)
        assert event is not None
        content = json.loads(event.content)
        assert event.kind == TREASURY_EVENT_KIND
        assert event.pub_key == treasurer.public_key_hex()
        assert content["action"] == "cmu:create"
        assert content["grant_id"] == "grant-id"
        assert content["mint"] == "https://clear.example"
        assert content["name"] == "Gym Guest Passes"
        assert content["unit_alias"] == "passes"
        return {
            "unit": "cmu-created",
            "keyset_id": "keyset-created",
            "friendly_name": content["name"],
            "friendly_unit_alias": content["unit_alias"],
            "status": "active",
        }

    monkeypatch.setattr(treasury_cli, "request_json", fake_request_json)
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-treasury",
            "--mint",
            "https://clear.example/",
            "--nsec",
            treasurer.private_key_bech32(),
            "cmu",
            "create",
            "grant-id",
            "--name",
            "Gym Guest Passes",
            "--unit-alias",
            "passes",
        ],
    )

    assert treasury_cli.main() == 0
    output = json.loads(capsys.readouterr().out)

    assert output["unit"] == "cmu-created"
    assert output["friendly_unit_alias"] == "passes"
    assert output["treasurer_npub"] == treasurer.public_key_bech32()
    assert calls[0][:3] == (
        "https://clear.example",
        "POST",
        "/v1/treasury/cmus",
    )
    assert calls[0][4] is None


def test_treasury_cli_cmu_info_signs_and_posts_envelope(monkeypatch, capsys) -> None:
    calls = []
    treasurer = Keys(priv_k="1".zfill(64))

    def fake_request_json(mint_url, method, path, payload=None, *, token=None):
        calls.append((mint_url, method, path, payload, token))
        event = Event.load(payload["event"], validate=True)
        assert event is not None
        content = json.loads(event.content)
        assert event.kind == TREASURY_EVENT_KIND
        assert event.pub_key == treasurer.public_key_hex()
        assert content["action"] == "cmu:info"
        assert content["mint"] == "https://clear.example"
        return {
            "unit": "cmu-created",
            "keyset_id": "keyset-created",
            "friendly_name": "Gym Guest Passes",
            "status": "active",
            "treasurer_npub": treasurer.public_key_bech32(),
        }

    monkeypatch.setattr(treasury_cli, "request_json", fake_request_json)
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-treasury",
            "--mint",
            "https://clear.example/",
            "--nsec",
            treasurer.private_key_bech32(),
            "cmu",
            "info",
            "--keyset-id",
            "keyset-created",
        ],
    )

    assert treasury_cli.main() == 0
    output = json.loads(capsys.readouterr().out)

    assert output["unit"] == "cmu-created"
    assert output["treasurer_npub"] == treasurer.public_key_bech32()
    assert calls[0][:3] == (
        "https://clear.example",
        "POST",
        "/v1/treasury/cmus/info",
    )
    assert calls[0][4] is None
    event = Event.load(calls[0][3]["event"], validate=True)
    assert event is not None
    assert json.loads(event.content)["keyset_id"] == "keyset-created"


def test_treasury_cli_cmu_summary_signs_and_posts_envelope(
    monkeypatch,
    capsys,
) -> None:
    calls = []
    treasurer = Keys(priv_k="1".zfill(64))

    def fake_request_json(mint_url, method, path, payload=None, *, token=None):
        calls.append((mint_url, method, path, payload, token))
        event = Event.load(payload["event"], validate=True)
        assert event is not None
        content = json.loads(event.content)
        assert event.kind == TREASURY_EVENT_KIND
        assert event.pub_key == treasurer.public_key_hex()
        assert content["action"] == "cmu:summary"
        assert content["mint"] == "https://clear.example"
        return {
            "unit": "cmu-created",
            "keyset_id": "keyset-created",
            "issued": 25,
            "retired": 5,
            "circulating": 20,
            "outstanding": 20,
            "treasurer_pubkey": treasurer.public_key_hex(),
        }

    monkeypatch.setattr(treasury_cli, "request_json", fake_request_json)
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-treasury",
            "--mint",
            "https://clear.example/",
            "--nsec",
            treasurer.private_key_bech32(),
            "cmu",
            "summary",
            "--keyset-id",
            "keyset-created",
        ],
    )

    assert treasury_cli.main() == 0
    output = json.loads(capsys.readouterr().out)

    assert output["unit"] == "cmu-created"
    assert output["outstanding"] == 20
    assert output["treasurer_npub"] == treasurer.public_key_bech32()
    assert calls[0][:3] == (
        "https://clear.example",
        "POST",
        "/v1/treasury/cmus/summary",
    )
    assert calls[0][4] is None
    event = Event.load(calls[0][3]["event"], validate=True)
    assert event is not None
    assert json.loads(event.content)["keyset_id"] == "keyset-created"


def test_treasury_cli_cmu_private_signs_and_posts_envelope(
    monkeypatch,
    capsys,
) -> None:
    calls = []
    treasurer = Keys(priv_k="1".zfill(64))

    def fake_request_json(mint_url, method, path, payload=None, *, token=None):
        calls.append((mint_url, method, path, payload, token))
        event = Event.load(payload["event"], validate=True)
        assert event is not None
        content = json.loads(event.content)
        assert event.kind == TREASURY_EVENT_KIND
        assert event.pub_key == treasurer.public_key_hex()
        assert content["action"] == "cmu:visibility"
        assert content["mint"] == "https://clear.example"
        assert content["keyset_id"] == "keyset-created"
        assert content["public_listing"] is False
        return {
            "unit": "cmu-created",
            "keyset_id": "keyset-created",
            "public_listing": False,
            "status": "active",
            "treasurer_npub": treasurer.public_key_bech32(),
        }

    monkeypatch.setattr(treasury_cli, "request_json", fake_request_json)
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-treasury",
            "--mint",
            "https://clear.example/",
            "--nsec",
            treasurer.private_key_bech32(),
            "cmu",
            "private",
            "--keyset-id",
            "keyset-created",
        ],
    )

    assert treasury_cli.main() == 0
    output = json.loads(capsys.readouterr().out)

    assert output["public_listing"] is False
    assert output["treasurer_npub"] == treasurer.public_key_bech32()
    assert calls[0][:3] == (
        "https://clear.example",
        "POST",
        "/v1/treasury/cmus/visibility",
    )
    assert calls[0][4] is None


def test_treasury_cli_cmu_publish_accepts_cmu_id(monkeypatch, capsys) -> None:
    calls = []
    treasurer = Keys(priv_k="1".zfill(64))

    def fake_request_json(mint_url, method, path, payload=None, *, token=None):
        calls.append((mint_url, method, path, payload, token))
        if path == "/v1/keysets":
            return {
                "keysets": [
                    {"id": "keyset-created", "unit": "cmu-created"},
                    {"id": "other-keyset", "unit": "cmu-other"},
                ]
            }
        event = Event.load(payload["event"], validate=True)
        assert event is not None
        content = json.loads(event.content)
        assert content["action"] == "cmu:visibility"
        assert content["keyset_id"] == "keyset-created"
        assert content["public_listing"] is True
        return {
            "unit": "cmu-created",
            "keyset_id": "keyset-created",
            "public_listing": True,
            "status": "active",
        }

    monkeypatch.setattr(treasury_cli, "request_json", fake_request_json)
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-treasury",
            "--mint",
            "https://clear.example/",
            "--nsec",
            treasurer.private_key_bech32(),
            "cmu",
            "publish",
            "--cmu-id",
            "cmu-created",
        ],
    )

    assert treasury_cli.main() == 0
    output = json.loads(capsys.readouterr().out)

    assert output["public_listing"] is True
    assert calls[0][:3] == ("https://clear.example", "GET", "/v1/keysets")
    assert calls[1][:3] == (
        "https://clear.example",
        "POST",
        "/v1/treasury/cmus/visibility",
    )


def test_treasury_cli_cmu_info_accepts_cmu_id(monkeypatch, capsys) -> None:
    calls = []
    treasurer = Keys(priv_k="1".zfill(64))

    def fake_request_json(mint_url, method, path, payload=None, *, token=None):
        calls.append((mint_url, method, path, payload, token))
        if path == "/v1/keysets":
            return {
                "keysets": [
                    {"id": "keyset-created", "unit": "cmu-created"},
                    {"id": "other-keyset", "unit": "cmu-other"},
                ]
            }
        event = Event.load(payload["event"], validate=True)
        assert event is not None
        content = json.loads(event.content)
        assert content["keyset_id"] == "keyset-created"
        return {
            "unit": "cmu-created",
            "keyset_id": "keyset-created",
            "friendly_name": "Gym Guest Passes",
            "status": "active",
        }

    monkeypatch.setattr(treasury_cli, "request_json", fake_request_json)
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-treasury",
            "--mint",
            "https://clear.example/",
            "--nsec",
            treasurer.private_key_bech32(),
            "cmu",
            "info",
            "--cmu-id",
            "cmu-created",
        ],
    )

    assert treasury_cli.main() == 0
    output = json.loads(capsys.readouterr().out)

    assert output["keyset_id"] == "keyset-created"
    assert calls[0][:3] == ("https://clear.example", "GET", "/v1/keysets")
    assert calls[1][:3] == (
        "https://clear.example",
        "POST",
        "/v1/treasury/cmus/info",
    )


def test_treasury_cli_issue_deposits_to_treasurer_wallet(
    monkeypatch, capsys, tmp_path
) -> None:
    treasurer = Keys(priv_k="1".zfill(64))
    wallet_path = tmp_path / "treasurer-wallet.json"

    def fake_issue_treasury_units(
        mint_url,
        nsec,
        amount,
        *,
        keyset_id=None,
        memo=None,
        lifetime_seconds=300,
    ):
        assert mint_url == "https://clear.example"
        assert nsec == treasurer.private_key_bech32()
        assert amount == 13
        assert keyset_id == "keyset-created"
        assert memo == "Workshop credits"
        assert lifetime_seconds == 300
        return {
            "mint": mint_url,
            "unit": "cmu-created",
            "keyset_id": "keyset-created",
            "quote": "quote-id",
            "amount": amount,
            "memo": memo,
            "token": "cashuAtoken",
            "proofs": [
                {"amount": 8, "id": "keyset-created", "secret": "s1", "C": "c1"},
                {"amount": 4, "id": "keyset-created", "secret": "s2", "C": "c2"},
                {"amount": 1, "id": "keyset-created", "secret": "s3", "C": "c3"},
            ],
        }

    monkeypatch.setattr(
        treasury_cli,
        "issue_treasury_units",
        fake_issue_treasury_units,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-treasury",
            "--mint",
            "https://clear.example",
            "--nsec",
            treasurer.private_key_bech32(),
            "--wallet",
            str(wallet_path),
            "issue",
            "13",
            "--keyset-id",
            "keyset-created",
            "--memo",
            "Workshop credits",
        ],
    )

    assert treasury_cli.main() == 0
    output = json.loads(capsys.readouterr().out)

    assert output["amount"] == 13
    assert output["treasurer_npub"] == treasurer.public_key_bech32()
    assert output["wallet"]["wallet"] == str(wallet_path)
    assert output["wallet"]["balances"] == [
        {"mint": "https://clear.example", "unit": "cmu-created", "amount": 13}
    ]


def test_treasury_cli_issue_accepts_cmu_id(monkeypatch, capsys) -> None:
    calls = []
    treasurer = Keys(priv_k="1".zfill(64))

    def fake_request_json(mint_url, method, path, payload=None, *, token=None):
        calls.append((mint_url, method, path, payload, token))
        return {"keysets": [{"id": "keyset-created", "unit": "cmu-created"}]}

    def fake_issue_treasury_units(
        mint_url,
        nsec,
        amount,
        *,
        keyset_id=None,
        memo=None,
        lifetime_seconds=300,
    ):
        assert keyset_id == "keyset-created"
        return {
            "mint": mint_url,
            "unit": "cmu-created",
            "keyset_id": "keyset-created",
            "quote": "quote-id",
            "amount": amount,
            "memo": memo,
            "token": "cashuAtoken",
            "proofs": [],
        }

    monkeypatch.setattr(treasury_cli, "request_json", fake_request_json)
    monkeypatch.setattr(
        treasury_cli,
        "issue_treasury_units",
        fake_issue_treasury_units,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-treasury",
            "--mint",
            "https://clear.example",
            "--nsec",
            treasurer.private_key_bech32(),
            "issue",
            "13",
            "--cmu-id",
            "cmu-created",
            "--to-token",
        ],
    )

    assert treasury_cli.main() == 0
    output = json.loads(capsys.readouterr().out)

    assert output["keyset_id"] == "keyset-created"
    assert calls[0][:3] == ("https://clear.example", "GET", "/v1/keysets")


def test_treasury_cli_rejects_unknown_cmu_id(monkeypatch, capsys) -> None:
    treasurer = Keys(priv_k="1".zfill(64))
    monkeypatch.setattr(
        treasury_cli,
        "request_json",
        lambda *args, **kwargs: {
            "keysets": [{"id": "keyset-created", "unit": "cmu-created"}]
        },
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-treasury",
            "--mint",
            "https://clear.example",
            "--nsec",
            treasurer.private_key_bech32(),
            "issue",
            "13",
            "--cmu-id",
            "cmu-missing",
        ],
    )

    assert treasury_cli.main() == 1
    assert "CMU was not found: cmu-missing" in capsys.readouterr().err


def test_treasury_cli_wallet_balance_uses_scoped_default_wallet(
    monkeypatch, capsys, tmp_path
) -> None:
    treasurer = Keys(priv_k="1".zfill(64))
    monkeypatch.setattr(treasury_cli, "DEFAULT_TREASURY_WALLET_BASE", tmp_path)
    wallet_path = treasury_cli._wallet_path(
        argparse.Namespace(
            mint="https://clear.example",
            nsec=treasurer.private_key_bech32(),
            wallet=None,
        ),
        treasurer.private_key_bech32(),
    )
    wallet_path.parent.mkdir(parents=True)
    wallet_path.write_text(
        json.dumps(
            {
                "version": 1,
                "entries": [
                    {
                        "mint": "https://clear.example",
                        "unit": "cmu-created",
                        "quote": "quote-id",
                        "amount": 8,
                        "memo": None,
                        "proofs": [
                            {
                                "amount": 8,
                                "id": "keyset-created",
                                "secret": "s1",
                                "C": "c1",
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-treasury",
            "--mint",
            "https://clear.example",
            "--nsec",
            treasurer.private_key_bech32(),
            "wallet",
            "balance",
        ],
    )

    assert treasury_cli.main() == 0
    output = json.loads(capsys.readouterr().out)

    assert output["treasurer_npub"] == treasurer.public_key_bech32()
    assert output["wallet"] == str(wallet_path)
    assert output["balances"] == [
        {"mint": "https://clear.example", "unit": "cmu-created", "amount": 8}
    ]


def test_treasury_wallet_default_path_is_scoped_by_nsec_and_mint(
    monkeypatch, tmp_path
) -> None:
    first = Keys(priv_k="1".zfill(64))
    second = Keys(priv_k="2".zfill(64))
    monkeypatch.setattr(treasury_cli, "DEFAULT_TREASURY_WALLET_BASE", tmp_path)

    first_path = treasury_cli._wallet_path(
        argparse.Namespace(mint="https://clear.example", nsec=None, wallet=None),
        first.private_key_bech32(),
    )
    second_path = treasury_cli._wallet_path(
        argparse.Namespace(mint="https://clear.example", nsec=None, wallet=None),
        second.private_key_bech32(),
    )
    other_mint_path = treasury_cli._wallet_path(
        argparse.Namespace(mint="https://other.example", nsec=None, wallet=None),
        first.private_key_bech32(),
    )

    assert first.public_key_bech32() in str(first_path)
    assert second.public_key_bech32() in str(second_path)
    assert first_path != second_path
    assert first_path != other_mint_path


def test_treasury_cli_send_delivers_exact_token_from_wallet(
    monkeypatch, capsys, tmp_path
) -> None:
    treasurer = Keys(priv_k="1".zfill(64))
    wallet_path = tmp_path / "treasury-wallet.json"
    deposit_issue(
        {
            "mint": "https://clear.example",
            "unit": "cmu-other",
            "quote": "other-quote-id",
            "amount": 13,
            "memo": None,
            "proofs": [
                {"amount": 8, "id": "other-keyset", "secret": "o1", "C": "oc1"},
                {"amount": 4, "id": "other-keyset", "secret": "o2", "C": "oc2"},
                {"amount": 1, "id": "other-keyset", "secret": "o3", "C": "oc3"},
            ],
        },
        wallet_path,
    )
    deposit_issue(
        {
            "mint": "https://clear.example",
            "unit": "cmu-created",
            "quote": "quote-id",
            "amount": 13,
            "memo": None,
            "proofs": [
                {"amount": 8, "id": "keyset-created", "secret": "s1", "C": "c1"},
                {"amount": 4, "id": "keyset-created", "secret": "s2", "C": "c2"},
                {"amount": 1, "id": "keyset-created", "secret": "s3", "C": "c3"},
            ],
        },
        wallet_path,
    )

    monkeypatch.setattr(
        treasury_cli,
        "_cmu_info",
        lambda mint, nsec, lifetime_seconds, *, keyset_id=None: {
            "unit": "cmu-created",
            "keyset_id": "keyset-created",
        },
    )
    monkeypatch.setattr(
        treasury_cli,
        "discover_clear_support",
        lambda address, *, mint_url, unit: {
            "address": address,
            "supported": True,
            "mint": mint_url,
            "unit": unit,
            "recipient_pubkey": "22" * 32,
            "relays": ["wss://relay.example"],
        },
    )

    def fake_deliver(
        discovery,
        *,
        token,
        amount,
        sender_secret=None,
        memo=None,
        relays=None,
        expiration=None,
    ):
        assert token.startswith("cashuA")
        decoded = decode_token_v3(token)
        assert decoded["unit"] == "cmu-created"
        assert {proof["id"] for proof in decoded["token"][0]["proofs"]} == {
            "keyset-created"
        }
        assert amount == 13
        assert sender_secret is None
        assert memo == "Gift"
        assert relays == ["wss://override.example"]
        assert expiration == 123
        return {
            "delivery": discovery,
            "publish": {"status": "OK", "verified": True},
        }

    monkeypatch.setattr(treasury_cli, "deliver_clear_token", fake_deliver)
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-treasury",
            "--mint",
            "https://clear.example",
            "--nsec",
            treasurer.private_key_bech32(),
            "--wallet",
            str(wallet_path),
            "send",
            "13",
            "alice@example.com",
            "--keyset-id",
            "keyset-created",
            "--memo",
            "Gift",
            "--relay",
            "wss://override.example",
            "--expiration",
            "123",
        ],
    )

    assert treasury_cli.main() == 0
    output = json.loads(capsys.readouterr().out)

    assert output["amount"] == 13
    assert output["unit"] == "cmu-created"
    assert output["treasurer_npub"] == treasurer.public_key_bech32()
    assert output["publish"]["verified"] is True
    assert treasury_cli.wallet_summary(load_wallet(wallet_path), wallet_path)[
        "balances"
    ] == [{"mint": "https://clear.example", "unit": "cmu-other", "amount": 13}]


def test_treasury_cli_send_rejects_internal_mint_before_discovery(
    monkeypatch, capsys
) -> None:
    treasurer = Keys(priv_k="1".zfill(64))
    monkeypatch.setattr(
        treasury_cli,
        "_cmu_info",
        lambda mint, nsec, lifetime_seconds, *, keyset_id=None: {
            "unit": "cmu-created",
            "keyset_id": "keyset-created",
        },
    )

    def unexpected_discovery(*args, **kwargs):
        raise AssertionError("internal mint delivery must stop before discovery")

    monkeypatch.setattr(
        treasury_cli,
        "discover_clear_support",
        unexpected_discovery,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-treasury",
            "--mint",
            "http://clear:3339",
            "--nsec",
            treasurer.private_key_bech32(),
            "send",
            "20",
            "alice@example.com",
            "--keyset-id",
            "keyset-created",
        ],
    )

    assert treasury_cli.main() == 1
    assert "internal-only mint" in capsys.readouterr().err


def test_treasury_cli_internal_mint_override_requires_explicit_relay(
    monkeypatch, capsys
) -> None:
    treasurer = Keys(priv_k="1".zfill(64))
    monkeypatch.setattr(
        treasury_cli,
        "_cmu_info",
        lambda mint, nsec, lifetime_seconds, *, keyset_id=None: {
            "unit": "cmu-created",
            "keyset_id": "keyset-created",
        },
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-treasury",
            "--mint",
            "http://clear:3339",
            "--nsec",
            treasurer.private_key_bech32(),
            "send",
            "20",
            "alice@example.com",
            "--keyset-id",
            "keyset-created",
            "--allow-internal-mint-delivery",
        ],
    )

    assert treasury_cli.main() == 1
    assert "requires at least one explicit --relay" in capsys.readouterr().err


def test_treasury_cli_send_swaps_when_exact_amount_is_unavailable(
    monkeypatch, tmp_path
) -> None:
    treasurer = Keys(priv_k="1".zfill(64))
    wallet_path = tmp_path / "treasury-wallet.json"
    deposit_issue(
        {
            "mint": "https://clear.example",
            "unit": "cmu-other",
            "quote": "other-quote-id",
            "amount": 16,
            "memo": None,
            "proofs": [
                {"amount": 16, "id": "other-keyset", "secret": "o16", "C": "oc16"},
            ],
        },
        wallet_path,
    )
    deposit_issue(
        {
            "mint": "https://clear.example",
            "unit": "cmu-created",
            "quote": "quote-id",
            "amount": 16,
            "memo": None,
            "proofs": [
                {"amount": 16, "id": "keyset-created", "secret": "s16", "C": "c16"},
            ],
        },
        wallet_path,
    )

    monkeypatch.setattr(
        treasury_cli,
        "_cmu_info",
        lambda mint, nsec, lifetime_seconds, *, keyset_id=None: {
            "unit": "cmu-created",
            "keyset_id": "keyset-created",
        },
    )
    monkeypatch.setattr(
        treasury_cli,
        "discover_clear_support",
        lambda address, *, mint_url, unit: {
            "address": address,
            "supported": True,
            "mint": mint_url,
            "unit": unit,
            "recipient_pubkey": "22" * 32,
            "relays": ["wss://relay.example"],
        },
    )

    def fake_swap(mint_url, inputs, amount, *, unit, memo=None):
        assert mint_url == "https://clear.example"
        assert inputs == [
            {"amount": 16, "id": "keyset-created", "secret": "s16", "C": "c16"}
        ]
        assert amount == 13
        assert unit == "cmu-created"
        return {
            "mint": mint_url,
            "unit": unit,
            "amount": amount,
            "input_amount": 16,
            "change_amount": 3,
            "token": "cashuAsend",
            "proofs": [
                {"amount": 8, "id": "keyset-created", "secret": "s8", "C": "c8"},
                {"amount": 4, "id": "keyset-created", "secret": "s4", "C": "c4"},
                {"amount": 1, "id": "keyset-created", "secret": "s1", "C": "c1"},
            ],
            "change_proofs": [
                {"amount": 2, "id": "keyset-created", "secret": "s2", "C": "c2"},
                {"amount": 1, "id": "keyset-created", "secret": "s3", "C": "c3"},
            ],
        }

    monkeypatch.setattr(treasury_cli, "swap_token_for_amount", fake_swap)
    monkeypatch.setattr(
        treasury_cli,
        "deliver_clear_token",
        lambda *args, **kwargs: {
            "delivery": {},
            "publish": {"status": "OK", "verified": True},
        },
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-treasury",
            "--mint",
            "https://clear.example",
            "--nsec",
            treasurer.private_key_bech32(),
            "--wallet",
            str(wallet_path),
            "send",
            "13",
            "alice@example.com",
            "--keyset-id",
            "keyset-created",
        ],
    )

    assert treasury_cli.main() == 0
    summary = treasury_cli.wallet_summary(load_wallet(wallet_path), wallet_path)
    assert summary["balances"] == [
        {"mint": "https://clear.example", "unit": "cmu-created", "amount": 3},
        {"mint": "https://clear.example", "unit": "cmu-other", "amount": 16},
    ]


def test_treasury_cli_issue_requires_cmu_selector(monkeypatch, capsys) -> None:
    treasurer = Keys(priv_k="1".zfill(64))
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-treasury",
            "--mint",
            "https://clear.example",
            "--nsec",
            treasurer.private_key_bech32(),
            "issue",
            "13",
        ],
    )

    with pytest.raises(SystemExit) as exc:
        treasury_cli.main()
    assert exc.value.code == 2
    error = capsys.readouterr().err
    assert "--keyset-id" in error
    assert "--cmu-id" in error


def test_treasury_cli_requires_nsec(monkeypatch, capsys) -> None:
    monkeypatch.delenv("CLEAR_TREASURER_NSEC", raising=False)
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-treasury",
            "--mint",
            "https://clear.example",
            "cmu",
            "create",
            "grant-id",
        ],
    )

    assert treasury_cli.main() == 1
    assert "treasurer nsec must be supplied" in capsys.readouterr().err
