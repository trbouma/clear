from __future__ import annotations

import argparse
import json

from stroma import Event, Keys

from clear import treasury_cli
from clear.root_wallet import deposit_issue, load_wallet
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
        memo=None,
        lifetime_seconds=300,
    ):
        assert mint_url == "https://clear.example"
        assert nsec == treasurer.private_key_bech32()
        assert amount == 13
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
        lambda mint, nsec, lifetime_seconds: {
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
    assert output["treasurer_npub"] == treasurer.public_key_bech32()
    assert output["publish"]["verified"] is True
    assert load_wallet(wallet_path)["entries"] == []


def test_treasury_cli_send_swaps_when_exact_amount_is_unavailable(
    monkeypatch, tmp_path
) -> None:
    treasurer = Keys(priv_k="1".zfill(64))
    wallet_path = tmp_path / "treasury-wallet.json"
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
        lambda mint, nsec, lifetime_seconds: {
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
        ],
    )

    assert treasury_cli.main() == 0
    summary = treasury_cli.wallet_summary(load_wallet(wallet_path), wallet_path)
    assert summary["balances"] == [
        {"mint": "https://clear.example", "unit": "cmu-created", "amount": 3}
    ]


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
