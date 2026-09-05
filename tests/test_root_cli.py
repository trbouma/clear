from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from clear import root_cli


def test_root_cli_is_the_primary_parser_name() -> None:
    assert root_cli.parser().prog == "clear-root"


def test_root_cli_error_uses_invoked_program_name(monkeypatch, capsys) -> None:
    monkeypatch.setattr("sys.argv", ["clear-root", "config"])

    assert root_cli.main() == 1

    assert capsys.readouterr().err.startswith("clear-root config failed:")


def test_root_cli_requires_loopback_api_url(monkeypatch) -> None:
    monkeypatch.setenv("CLEAR_ROOT_API_URL", "https://clear.example")

    with pytest.raises(root_cli.TreasuryError, match="requires a loopback API URL"):
        root_cli._api_url(SimpleNamespace(api_url=None))


def test_root_cli_prefers_root_api_url(monkeypatch) -> None:
    monkeypatch.setenv("CLEAR_ROOT_API_URL", "http://localhost:3340/")

    assert root_cli._api_url(SimpleNamespace(api_url=None)) == "http://localhost:3340"


@pytest.mark.parametrize(
    ("arguments", "method", "path", "payload"),
    [
        (["verify"], "POST", "/v1/operator/commissioning/verify", None),
        (["treasury", "status"], "GET", "/v1/operator/treasury", None),
        (["treasury", "enable"], "POST", "/v1/operator/treasury/enable", None),
        (
            ["treasury", "disable", "--reason", "maintenance"],
            "POST",
            "/v1/operator/treasury/disable",
            {"reason": "maintenance"},
        ),
    ],
)
def test_root_cli_commissioning_commands_use_operator_api(
    arguments,
    method,
    path,
    payload,
    monkeypatch,
    capsys,
) -> None:
    calls = []
    monkeypatch.setenv("CLEAR_OPERATOR_TOKEN", "operator-token")
    monkeypatch.setenv("CLEAR_ROOT_API_URL", "http://127.0.0.1:3339")

    def fake_request_json(
        mint_url, request_method, request_path, body=None, *, token=None
    ):
        calls.append((mint_url, request_method, request_path, body, token))
        return {"lifecycle": "root-verified", "treasury_enabled": False}

    monkeypatch.setattr(root_cli, "request_json", fake_request_json)
    monkeypatch.setattr("sys.argv", ["clear-root", *arguments])

    assert root_cli.main() == 0
    assert '"lifecycle": "root-verified"' in capsys.readouterr().out
    assert calls == [
        (
            "http://127.0.0.1:3339",
            method,
            path,
            payload,
            "operator-token",
        )
    ]


def test_root_cli_does_not_fall_back_to_public_mint_url(monkeypatch) -> None:
    monkeypatch.delenv("CLEAR_ROOT_API_URL", raising=False)
    monkeypatch.setenv("CLEAR_MINT_URL", "https://clear.example/")

    assert root_cli._api_url(SimpleNamespace(api_url=None)) == root_cli.DEFAULT_MINT_URL


def test_root_cli_migrates_legacy_wallet_file(tmp_path) -> None:
    legacy = tmp_path / "clear-lab-wallet.json"
    root_wallet = tmp_path / "clear-root-wallet.json"
    legacy.write_text('{"version": 1, "entries": []}\n', encoding="utf-8")

    selected = root_cli._wallet_path(SimpleNamespace(wallet=str(root_wallet)))

    assert selected == root_wallet
    assert root_wallet.exists()
    assert not legacy.exists()


def test_root_cli_config_writes_display_metadata(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    env_file = tmp_path / ".env"
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-root",
            "config",
            "--env-file",
            str(env_file),
            "--currency-name",
            "Harbour Credits",
            "--currency-alias",
            "Harbour Lab Credits",
            "--currency-unit-alias",
            "smiles",
            "--root-authority-npub",
            "npub1root",
            "--mint-url",
            "http://127.0.0.1:3339",
        ],
    )

    assert root_cli.main() == 0

    assert env_file.read_text(encoding="utf-8") == (
        'CLEAR_CURRENCY_NAME="Harbour Credits"\n'
        'CLEAR_CURRENCY_ALIAS="Harbour Lab Credits"\n'
        'CLEAR_CURRENCY_UNIT_ALIAS="smiles"\n'
        'CLEAR_ROOT_AUTHORITY_NPUB="npub1root"\n'
        'CLEAR_MINT_URL="http://127.0.0.1:3339"\n'
    )
    assert '"CLEAR_CURRENCY_UNIT_ALIAS": "smiles"' in capsys.readouterr().out


def test_root_cli_config_preserves_existing_secrets(tmp_path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "CLEAR_MASTER_SECRET=secret",
                "CLEAR_OPERATOR_TOKEN=token",
                "CLEAR_CURRENCY_ALIAS=Old Alias",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-root",
            "config",
            "--env-file",
            str(env_file),
            "--currency-alias",
            "New Alias",
        ],
    )

    assert root_cli.main() == 0

    assert env_file.read_text(encoding="utf-8") == (
        "CLEAR_MASTER_SECRET=secret\n"
        "CLEAR_OPERATOR_TOKEN=token\n"
        'CLEAR_CURRENCY_ALIAS="New Alias"\n'
    )


def test_root_cli_issue_to_token_uses_dotenv_operator_token(
    monkeypatch,
    capsys,
) -> None:
    issued = {
        "mint": "http://127.0.0.1:3339",
        "unit": "cmu-0011223344556677",
        "quote": "quote-id",
        "amount": 21,
        "memo": "test",
        "token": "cashuAtoken",
        "proofs": [],
    }
    monkeypatch.setenv("CLEAR_OPERATOR_TOKEN", "operator-token")
    monkeypatch.setattr(
        root_cli,
        "issue_units",
        lambda mint_url, operator_token, amount, *, memo=None: issued,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-root",
            "--mint-url",
            "http://127.0.0.1:3339",
            "issue",
            "21",
            "--memo",
            "test",
            "--to-token",
        ],
    )

    assert root_cli.main() == 0
    output = capsys.readouterr().out

    assert '"token": "cashuAtoken"' in output


def test_root_cli_issue_stores_to_local_wallet_by_default(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    wallet_path = tmp_path / "clear-root-wallet.json"
    issued = {
        "mint": "http://127.0.0.1:3339",
        "unit": "cmu-0011223344556677",
        "quote": "quote-id",
        "amount": 21,
        "memo": "test",
        "token": "cashuAtoken",
        "proofs": [
            {"amount": 16, "id": "keyset-id", "secret": "a", "C": "b"},
            {"amount": 4, "id": "keyset-id", "secret": "c", "C": "d"},
            {"amount": 1, "id": "keyset-id", "secret": "e", "C": "f"},
        ],
    }
    monkeypatch.setenv("CLEAR_OPERATOR_TOKEN", "operator-token")
    monkeypatch.setattr(
        root_cli,
        "issue_units",
        lambda mint_url, operator_token, amount, *, memo=None: issued,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-root",
            "--mint-url",
            "http://127.0.0.1:3339",
            "--wallet",
            str(wallet_path),
            "issue",
            "21",
            "--memo",
            "test",
        ],
    )

    assert root_cli.main() == 0
    output = capsys.readouterr().out

    assert '"wallet": "' in output
    assert '"amount": 21' in output
    assert "cashuAtoken" not in output
    assert '"proofs"' not in output
    assert wallet_path.exists()


def test_root_cli_withdraw_exports_from_local_wallet(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    wallet_path = tmp_path / "clear-root-wallet.json"
    wallet_path.write_text(
        """
{
  "version": 1,
  "entries": [
    {
      "mint": "http://127.0.0.1:3339",
      "unit": "cmu-0011223344556677",
      "quote": "quote-id",
      "amount": 5,
      "memo": "float",
      "proofs": [
        {"amount": 4, "id": "keyset-id", "secret": "a", "C": "b"},
        {"amount": 1, "id": "keyset-id", "secret": "c", "C": "d"}
      ]
    }
  ]
}
""".lstrip(),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-root",
            "--wallet",
            str(wallet_path),
            "withdraw",
            "5",
            "--memo",
            "send",
        ],
    )

    assert root_cli.main() == 0
    output = capsys.readouterr().out

    assert '"token": "cashuA' in output
    assert '"amount": 5' in output
    assert '"entries": []' in wallet_path.read_text(encoding="utf-8")


def test_root_cli_send_delivers_then_removes_from_local_wallet(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    wallet_path = tmp_path / "clear-root-wallet.json"
    wallet_path.write_text(
        """
{
  "version": 1,
  "entries": [
    {
      "mint": "http://127.0.0.1:3339",
      "unit": "cmu-0011223344556677",
      "quote": "quote-id",
      "amount": 5,
      "memo": "float",
      "proofs": [
        {"amount": 4, "id": "keyset-id", "secret": "a", "C": "b"},
        {"amount": 1, "id": "keyset-id", "secret": "c", "C": "d"}
      ]
    }
  ]
}
""".lstrip(),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        root_cli,
        "request_json",
        lambda mint_url, method, path, payload=None, *, token=None: {
            "currency": {"unit": "cmu-0011223344556677"}
        },
    )
    monkeypatch.setattr(
        root_cli,
        "discover_clear_support",
        lambda address, *, mint_url, unit: {
            "supported": True,
            "mint": mint_url,
            "unit": unit,
            "recipient_pubkey": "11" * 32,
            "relays": ["wss://relay.example"],
        },
    )
    monkeypatch.setattr(
        root_cli,
        "deliver_clear_token",
        lambda discovery,
        *,
        token,
        amount,
        sender_secret,
        memo=None,
        relays=None,
        expiration=None: {
            "delivery": discovery,
            "publish": {
                "status": "OK",
                "sender_ephemeral": sender_secret is None,
            },
        },
    )
    monkeypatch.setenv("CLEAR_ROOT_NSEC", "")
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-root",
            "--mint-url",
            "http://127.0.0.1:3339",
            "--wallet",
            str(wallet_path),
            "send",
            "5",
            "alice@example.com",
            "--memo",
            "send",
        ],
    )

    assert root_cli.main() == 0
    output = capsys.readouterr().out

    assert '"status": "OK"' in output
    assert '"sender_ephemeral": true' in output
    assert '"entries": []' in wallet_path.read_text(encoding="utf-8")


def test_root_cli_send_preserves_wallet_when_delivery_fails(
    tmp_path,
    monkeypatch,
) -> None:
    wallet_path = tmp_path / "clear-root-wallet.json"
    original = """
{
  "version": 1,
  "entries": [
    {
      "mint": "http://127.0.0.1:3339",
      "unit": "cmu-0011223344556677",
      "quote": "quote-id",
      "amount": 5,
      "memo": "float",
      "proofs": [
        {"amount": 4, "id": "keyset-id", "secret": "a", "C": "b"},
        {"amount": 1, "id": "keyset-id", "secret": "c", "C": "d"}
      ]
    }
  ]
}
""".lstrip()
    wallet_path.write_text(original, encoding="utf-8")
    monkeypatch.setattr(
        root_cli,
        "request_json",
        lambda mint_url, method, path, payload=None, *, token=None: {
            "currency": {"unit": "cmu-0011223344556677"}
        },
    )
    monkeypatch.setattr(
        root_cli,
        "discover_clear_support",
        lambda address, *, mint_url, unit: {
            "supported": True,
            "mint": mint_url,
            "unit": unit,
            "recipient_pubkey": "11" * 32,
            "relays": ["wss://relay.example"],
        },
    )

    def fail_delivery(
        discovery,
        *,
        token,
        amount,
        sender_secret,
        memo=None,
        relays=None,
        expiration=None,
    ):
        raise root_cli.DeliveryError("delivery failed")

    monkeypatch.setattr(root_cli, "deliver_clear_token", fail_delivery)
    monkeypatch.delenv("CLEAR_ROOT_NSEC", raising=False)
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-root",
            "--mint-url",
            "http://127.0.0.1:3339",
            "--wallet",
            str(wallet_path),
            "send",
            "5",
            "alice@example.com",
        ],
    )

    assert root_cli.main() == 1
    assert wallet_path.read_text(encoding="utf-8") == original


def test_root_cli_send_swaps_larger_proof_for_change(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    wallet_path = tmp_path / "clear-root-wallet.json"
    wallet_path.write_text(
        """
{
  "version": 1,
  "entries": [
    {
      "mint": "http://127.0.0.1:3339",
      "unit": "cmu-0011223344556677",
      "quote": "quote-id",
      "amount": 32,
      "memo": "float",
      "proofs": [
        {"amount": 32, "id": "keyset-id", "secret": "large", "C": "sig-large"}
      ]
    }
  ]
}
""".lstrip(),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        root_cli,
        "request_json",
        lambda mint_url, method, path, payload=None, *, token=None: {
            "currency": {"unit": "cmu-0011223344556677"}
        },
    )
    monkeypatch.setattr(
        root_cli,
        "discover_clear_support",
        lambda address, *, mint_url, unit: {
            "supported": True,
            "mint": mint_url,
            "unit": unit,
            "recipient_pubkey": "11" * 32,
            "relays": ["wss://relay.example"],
        },
    )
    monkeypatch.setattr(
        root_cli,
        "swap_token_for_amount",
        lambda mint_url, inputs, amount, *, unit, memo=None: {
            "mint": mint_url,
            "unit": unit,
            "amount": amount,
            "input_amount": 32,
            "change_amount": 7,
            "token": "cashuAswapped",
            "proofs": [
                {"amount": 16, "id": "keyset-id", "secret": "s16", "C": "c16"},
                {"amount": 8, "id": "keyset-id", "secret": "s8", "C": "c8"},
                {"amount": 1, "id": "keyset-id", "secret": "s1", "C": "c1"},
            ],
            "change_proofs": [
                {"amount": 4, "id": "keyset-id", "secret": "c4", "C": "cc4"},
                {"amount": 2, "id": "keyset-id", "secret": "c2", "C": "cc2"},
                {"amount": 1, "id": "keyset-id", "secret": "c1", "C": "cc1"},
            ],
        },
    )
    monkeypatch.setattr(
        root_cli,
        "deliver_clear_token",
        lambda discovery,
        *,
        token,
        amount,
        sender_secret,
        memo=None,
        relays=None,
        expiration=None: {"delivery": discovery, "publish": {"status": "OK"}},
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-root",
            "--mint-url",
            "http://127.0.0.1:3339",
            "--wallet",
            str(wallet_path),
            "send",
            "25",
            "alice@example.com",
            "--memo",
            "send",
        ],
    )

    assert root_cli.main() == 0
    output = capsys.readouterr().out
    wallet = json.loads(wallet_path.read_text(encoding="utf-8"))
    remaining_amount = sum(
        proof["amount"]
        for entry in wallet["entries"]
        for proof in entry["proofs"]
    )

    assert '"amount": 25' in output
    assert remaining_amount == 7


def test_root_cli_retire_reads_token_from_stdin(monkeypatch, capsys) -> None:
    retired = {
        "mint": "http://127.0.0.1:3339",
        "unit": "cmu-0011223344556677",
        "amount": 21,
        "status": "RETIRED",
        "memo": None,
    }
    monkeypatch.setenv("CLEAR_OPERATOR_TOKEN", "operator-token")
    monkeypatch.setattr("sys.stdin.read", lambda: "cashuAtoken")
    monkeypatch.setattr(
        root_cli,
        "retire_token",
        lambda mint_url, operator_token, token, *, memo=None: retired,
    )
    monkeypatch.setattr(
        "sys.argv",
        ["clear-root", "--mint-url", "http://127.0.0.1:3339", "retire"],
    )

    assert root_cli.main() == 0
    output = capsys.readouterr().out

    assert '"status": "RETIRED"' in output


def test_root_cli_retire_accepts_proof_json_from_stdin(monkeypatch, capsys) -> None:
    calls = []
    proof = {"amount": 8, "id": "keyset-id", "secret": "secret", "C": "signature"}
    monkeypatch.setenv("CLEAR_OPERATOR_TOKEN", "operator-token")
    monkeypatch.setattr(
        "sys.stdin.read",
        lambda: json.dumps({"unit": "cmu-test", "proofs": [proof]}),
    )

    def fake_retire(mint_url, operator_token, proofs, *, unit=None, memo=None):
        calls.append((mint_url, operator_token, proofs, unit, memo))
        return {
            "mint": mint_url,
            "unit": unit,
            "amount": 8,
            "status": "RETIRED",
            "memo": memo,
        }

    monkeypatch.setattr(root_cli, "retire_proofs", fake_retire)
    monkeypatch.setattr(
        "sys.argv",
        ["clear-root", "--mint-url", "http://127.0.0.1:3339", "retire"],
    )

    assert root_cli.main() == 0
    assert calls == [
        ("http://127.0.0.1:3339", "operator-token", [proof], "cmu-test", None)
    ]
    assert '"amount": 8' in capsys.readouterr().out


def test_root_cli_retire_amount_uses_local_wallet(
    monkeypatch, capsys, tmp_path
) -> None:
    wallet_path = tmp_path / "wallet.json"
    calls = []
    monkeypatch.setenv("CLEAR_OPERATOR_TOKEN", "operator-token")
    monkeypatch.setattr(
        root_cli,
        "_export_or_swap",
        lambda amount, path, *, api_url, memo=None: {
            "amount": amount,
            "token": "cashuAtoken",
        },
    )
    monkeypatch.setattr(
        root_cli,
        "retire_token",
        lambda mint_url, operator_token, token, *, memo=None: {
            "mint": mint_url,
            "unit": "cmu-test",
            "amount": 25,
            "status": "RETIRED",
            "memo": memo,
        },
    )

    def fake_export(amount, path, *, memo=None, remove=False):
        calls.append((amount, path, memo, remove))
        return {"amount": amount}

    monkeypatch.setattr(root_cli, "export_token", fake_export)
    monkeypatch.setattr(root_cli, "load_wallet", lambda path: {"entries": []})
    monkeypatch.setattr(
        root_cli,
        "wallet_summary",
        lambda wallet, path: {"wallet": str(path), "entries": 0, "balances": []},
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-root",
            "--mint-url",
            "http://127.0.0.1:3339",
            "--wallet",
            str(wallet_path),
            "retire",
            "25",
            "--memo",
            "expired",
        ],
    )

    assert root_cli.main() == 0
    assert calls == [(25, wallet_path, "expired", True)]
    output = capsys.readouterr().out
    assert '"status": "RETIRED"' in output
    assert '"wallet": "' in output


def test_root_cli_redeem_remains_a_retire_alias(monkeypatch, capsys) -> None:
    monkeypatch.setenv("CLEAR_OPERATOR_TOKEN", "operator-token")
    monkeypatch.setattr(
        root_cli,
        "retire_token",
        lambda mint_url, operator_token, token, *, memo=None: {
            "mint": mint_url,
            "unit": "cmu-test",
            "amount": 1,
            "status": "RETIRED",
            "memo": memo,
        },
    )
    monkeypatch.setattr(
        "sys.argv",
        ["clear-root", "--mint-url", "http://127.0.0.1:3339", "redeem", "cashuAtoken"],
    )

    assert root_cli.main() == 0
    assert '"status": "RETIRED"' in capsys.readouterr().out


def test_root_cli_summary_calls_operator_endpoint(monkeypatch, capsys) -> None:
    calls = []
    monkeypatch.setenv("CLEAR_OPERATOR_TOKEN", "operator-token")

    def fake_request_json(mint_url, method, path, payload=None, *, token=None):
        calls.append((mint_url, method, path, payload, token))
        return {
            "unit": "cmu-0011223344556677",
            "keyset_id": "keyset-id",
            "issued": 21,
            "retired": 8,
            "outstanding": 13,
        }

    monkeypatch.setattr(root_cli, "request_json", fake_request_json)
    monkeypatch.setattr(
        "sys.argv",
        ["clear-root", "--mint-url", "http://127.0.0.1:3339/", "summary"],
    )

    assert root_cli.main() == 0
    output = capsys.readouterr().out

    assert '"outstanding": 13' in output
    assert calls == [
        (
            "http://127.0.0.1:3339",
            "GET",
            "/v1/operator/summary",
            None,
            "operator-token",
        )
    ]


def test_root_cli_treasurer_add_calls_operator_endpoint(monkeypatch, capsys) -> None:
    calls = []
    monkeypatch.setenv("CLEAR_OPERATOR_TOKEN", "operator-token")

    def fake_request_json(mint_url, method, path, payload=None, *, token=None):
        calls.append((mint_url, method, path, payload, token))
        return {
            "npub": payload["npub"],
            "status": "active",
            "created": True,
        }

    monkeypatch.setattr(root_cli, "request_json", fake_request_json)
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-root",
            "--mint-url",
            "http://127.0.0.1:3339",
            "treasurer",
            "add",
            "npub1treasurer",
        ],
    )

    assert root_cli.main() == 0
    assert '"created": true' in capsys.readouterr().out
    assert calls == [
        (
            "http://127.0.0.1:3339",
            "POST",
            "/v1/operator/treasurers",
            {"npub": "npub1treasurer"},
            "operator-token",
        )
    ]


def test_root_cli_treasurer_list_calls_operator_endpoint(monkeypatch, capsys) -> None:
    calls = []
    monkeypatch.setenv("CLEAR_OPERATOR_TOKEN", "operator-token")

    def fake_request_json(mint_url, method, path, payload=None, *, token=None):
        calls.append((mint_url, method, path, payload, token))
        return {"treasurers": [{"npub": "npub1treasurer", "status": "active"}]}

    monkeypatch.setattr(root_cli, "request_json", fake_request_json)
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-root",
            "--mint-url",
            "http://127.0.0.1:3339",
            "treasurer",
            "list",
        ],
    )

    assert root_cli.main() == 0
    assert '"npub": "npub1treasurer"' in capsys.readouterr().out
    assert calls == [
        (
            "http://127.0.0.1:3339",
            "GET",
            "/v1/operator/treasurers",
            None,
            "operator-token",
        )
    ]


def test_root_cli_treasurer_grant_calls_operator_endpoint(monkeypatch, capsys) -> None:
    calls = []
    monkeypatch.setenv("CLEAR_OPERATOR_TOKEN", "operator-token")

    def fake_request_json(mint_url, method, path, payload=None, *, token=None):
        calls.append((mint_url, method, path, payload, token))
        return {
            "id": "grant-id",
            "npub": payload["npub"],
            "scope": "keyset:create",
            "status": "pending",
        }

    monkeypatch.setattr(root_cli, "request_json", fake_request_json)
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-root",
            "--mint-url",
            "http://127.0.0.1:3339",
            "treasurer",
            "grant",
            "npub1treasurer",
        ],
    )

    assert root_cli.main() == 0
    assert '"scope": "keyset:create"' in capsys.readouterr().out
    assert calls == [
        (
            "http://127.0.0.1:3339",
            "POST",
            "/v1/operator/treasurer-grants",
            {"npub": "npub1treasurer"},
            "operator-token",
        )
    ]


def test_root_cli_treasurer_grants_calls_operator_endpoint(monkeypatch, capsys) -> None:
    calls = []
    monkeypatch.setenv("CLEAR_OPERATOR_TOKEN", "operator-token")

    def fake_request_json(mint_url, method, path, payload=None, *, token=None):
        calls.append((mint_url, method, path, payload, token))
        return {"grants": [{"id": "grant-id", "status": "pending"}]}

    monkeypatch.setattr(root_cli, "request_json", fake_request_json)
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-root",
            "--mint-url",
            "http://127.0.0.1:3339",
            "treasurer",
            "grants",
        ],
    )

    assert root_cli.main() == 0
    assert '"grant-id"' in capsys.readouterr().out
    assert calls == [
        (
            "http://127.0.0.1:3339",
            "GET",
            "/v1/operator/treasurer-grants",
            None,
            "operator-token",
        )
    ]


def test_root_cli_treasurer_keygen_prints_pair_without_api_call(
    monkeypatch, capsys
) -> None:
    class FakeKeys:
        def public_key_bech32(self):
            return "npub1generated"

        def private_key_bech32(self):
            return "nsec1generated"

        def public_key_hex(self):
            return "11" * 32

        def private_key_hex(self):
            return "22" * 32

    monkeypatch.setattr(root_cli, "Keys", FakeKeys)

    def fail_request_json(*args, **kwargs):
        raise AssertionError("keygen should not contact the mint")

    monkeypatch.setattr(root_cli, "request_json", fail_request_json)
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-root",
            "treasurer",
            "keygen",
        ],
    )

    assert root_cli.main() == 0
    result = json.loads(capsys.readouterr().out)

    assert result["npub"].startswith("npub1")
    assert result["nsec"].startswith("nsec1")
    assert result["public_key"] == "11" * 32
    assert result["private_key"] == "22" * 32
    assert "mint must never store it" in result["warning"]


def test_root_cli_cmu_create_calls_operator_endpoint(monkeypatch, capsys) -> None:
    calls = []
    monkeypatch.setenv("CLEAR_OPERATOR_TOKEN", "operator-token")

    def fake_request_json(mint_url, method, path, payload=None, *, token=None):
        calls.append((mint_url, method, path, payload, token))
        return {
            "unit": "cmu-created",
            "keyset_id": "keyset-created",
            "friendly_name": payload["name"],
            "friendly_unit_alias": payload["unit_alias"],
            "status": "active",
        }

    monkeypatch.setattr(root_cli, "request_json", fake_request_json)
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-root",
            "--mint-url",
            "http://127.0.0.1:3339",
            "cmu",
            "create",
            "grant-id",
            "--name",
            "Gym Guest Passes",
            "--unit-alias",
            "passes",
        ],
    )

    assert root_cli.main() == 0
    assert '"unit": "cmu-created"' in capsys.readouterr().out
    assert calls == [
        (
            "http://127.0.0.1:3339",
            "POST",
            "/v1/operator/cmus",
            {
                "grant_id": "grant-id",
                "name": "Gym Guest Passes",
                "unit_alias": "passes",
            },
            "operator-token",
        )
    ]


def test_root_cli_cmu_list_calls_operator_endpoint(monkeypatch, capsys) -> None:
    calls = []
    monkeypatch.setenv("CLEAR_OPERATOR_TOKEN", "operator-token")

    def fake_request_json(mint_url, method, path, payload=None, *, token=None):
        calls.append((mint_url, method, path, payload, token))
        return {"cmus": [{"unit": "cmu-created", "status": "active"}]}

    monkeypatch.setattr(root_cli, "request_json", fake_request_json)
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-root",
            "--mint-url",
            "http://127.0.0.1:3339",
            "cmu",
            "list",
        ],
    )

    assert root_cli.main() == 0
    assert '"unit": "cmu-created"' in capsys.readouterr().out
    assert calls == [
        (
            "http://127.0.0.1:3339",
            "GET",
            "/v1/operator/cmus",
            None,
            "operator-token",
        )
    ]


def test_root_cli_cmu_label_calls_operator_endpoint(monkeypatch, capsys) -> None:
    calls = []
    monkeypatch.setenv("CLEAR_OPERATOR_TOKEN", "operator-token")

    def fake_request_json(mint_url, method, path, payload=None, *, token=None):
        calls.append((mint_url, method, path, payload, token))
        return {
            "unit": "cmu-created",
            "keyset_id": "keyset-created",
            "friendly_name": payload["name"],
            "friendly_unit_alias": payload["unit_alias"],
            "status": "active",
        }

    monkeypatch.setattr(root_cli, "request_json", fake_request_json)
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-root",
            "--mint-url",
            "http://127.0.0.1:3339",
            "cmu",
            "label",
            "cmu-created",
            "--name",
            "Food Share Credits",
            "--unit-alias",
            "shares",
        ],
    )

    assert root_cli.main() == 0
    assert '"friendly_name": "Food Share Credits"' in capsys.readouterr().out
    assert calls == [
        (
            "http://127.0.0.1:3339",
            "POST",
            "/v1/operator/cmus/cmu-created/label",
            {
                "name": "Food Share Credits",
                "unit_alias": "shares",
            },
            "operator-token",
        )
    ]


def test_root_cli_info_combines_cmu_metadata_and_circulation(
    monkeypatch,
    capsys,
) -> None:
    calls = []
    monkeypatch.setenv("CLEAR_OPERATOR_TOKEN", "operator-token")
    monkeypatch.setenv("CLEAR_ROOT_API_URL", "http://127.0.0.1:3339")
    monkeypatch.setenv("CLEAR_MINT_URL", "https://clear.example")

    def fake_request_json(mint_url, method, path, payload=None, *, token=None):
        calls.append((mint_url, method, path, payload, token))
        if path == "/v1/info":
            return {
                "name": "Clear",
                "version": "0.1.0",
                "mint_url": "https://clear.example",
                "description": "Example Credits issued as Clear ecash",
                "service_identity": {
                    "npub": "npub1service",
                    "type": "clear-mint",
                    "management": "mainstay-managed",
                    "state": "uncommissioned",
                },
                "currency": {
                    "name": "Example Credits",
                    "display_unit": "CMU",
                    "unit": "cmu-0011223344556677",
                    "keyset_fingerprint": "0011223344556677",
                    "keyset_id": "keyset-id",
                    "friendly_alias": "Example Credits (cmu-0011223344556677)",
                    "friendly_unit_alias": "smiles",
                    "friendly_alias_key": "example-credits:0011223344556677",
                },
                "policy": {
                    "mode": "root-bootstrap",
                    "root_authority_npub": "npub1root",
                    "enforced": False,
                },
            }
        if path == "/v1/operator/summary":
            return {
                "unit": "cmu-0011223344556677",
                "keyset_id": "keyset-id",
                "issued": 34,
                "retired": 13,
                "outstanding": 21,
            }
        raise AssertionError(path)

    monkeypatch.setattr(root_cli, "request_json", fake_request_json)
    monkeypatch.setattr(
        "sys.argv",
        ["clear-root", "info"],
    )

    assert root_cli.main() == 0
    output = capsys.readouterr().out

    assert '"unit": "cmu-0011223344556677"' in output
    assert '"mint": "https://clear.example"' in output
    assert '"api_url": "http://127.0.0.1:3339"' in output
    assert '"friendly_alias": "Example Credits (cmu-0011223344556677)"' in output
    assert '"friendly_unit_alias": "smiles"' in output
    assert '"root_authority_npub": "npub1root"' in output
    assert '"npub": "npub1service"' in output
    assert '"state": "uncommissioned"' in output
    assert '"issued": 34' in output
    assert '"retired": 13' in output
    assert '"circulating": 21' in output
    assert '"outstanding": 21' in output
    assert calls == [
        ("http://127.0.0.1:3339", "GET", "/v1/info", None, None),
        (
            "http://127.0.0.1:3339",
            "GET",
            "/v1/operator/summary",
            None,
            "operator-token",
        ),
    ]
