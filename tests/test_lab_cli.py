from __future__ import annotations

import json

from clear import lab_cli


def test_lab_cli_configure_writes_display_metadata(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    env_file = tmp_path / ".env"
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-lab",
            "configure",
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
            "http://127.0.0.1:3338",
        ],
    )

    assert lab_cli.main() == 0

    assert env_file.read_text(encoding="utf-8") == (
        'CLEAR_CURRENCY_NAME="Harbour Credits"\n'
        'CLEAR_CURRENCY_ALIAS="Harbour Lab Credits"\n'
        'CLEAR_CURRENCY_UNIT_ALIAS="smiles"\n'
        'CLEAR_ROOT_AUTHORITY_NPUB="npub1root"\n'
        'CLEAR_MINT_URL="http://127.0.0.1:3338"\n'
    )
    assert '"CLEAR_CURRENCY_UNIT_ALIAS": "smiles"' in capsys.readouterr().out


def test_lab_cli_configure_preserves_existing_secrets(tmp_path, monkeypatch) -> None:
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
            "clear-lab",
            "configure",
            "--env-file",
            str(env_file),
            "--currency-alias",
            "New Alias",
        ],
    )

    assert lab_cli.main() == 0

    assert env_file.read_text(encoding="utf-8") == (
        "CLEAR_MASTER_SECRET=secret\n"
        "CLEAR_OPERATOR_TOKEN=token\n"
        'CLEAR_CURRENCY_ALIAS="New Alias"\n'
    )


def test_lab_cli_issue_to_token_uses_dotenv_operator_token(
    monkeypatch,
    capsys,
) -> None:
    issued = {
        "mint": "http://clear.example",
        "unit": "cmu-0011223344556677",
        "quote": "quote-id",
        "amount": 21,
        "memo": "test",
        "token": "cashuAtoken",
        "proofs": [],
    }
    monkeypatch.setenv("CLEAR_OPERATOR_TOKEN", "operator-token")
    monkeypatch.setattr(
        lab_cli,
        "issue_token",
        lambda mint_url, operator_token, amount, *, memo=None: issued,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-lab",
            "--mint-url",
            "http://clear.example",
            "issue",
            "21",
            "--memo",
            "test",
            "--to-token",
        ],
    )

    assert lab_cli.main() == 0
    output = capsys.readouterr().out

    assert '"token": "cashuAtoken"' in output


def test_lab_cli_issue_stores_to_local_wallet_by_default(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    wallet_path = tmp_path / "clear-lab-wallet.json"
    issued = {
        "mint": "http://clear.example",
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
        lab_cli,
        "issue_token",
        lambda mint_url, operator_token, amount, *, memo=None: issued,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-lab",
            "--mint-url",
            "http://clear.example",
            "--wallet",
            str(wallet_path),
            "issue",
            "21",
            "--memo",
            "test",
        ],
    )

    assert lab_cli.main() == 0
    output = capsys.readouterr().out

    assert '"wallet": "' in output
    assert '"amount": 21' in output
    assert wallet_path.exists()


def test_lab_cli_withdraw_exports_from_local_wallet(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    wallet_path = tmp_path / "clear-lab-wallet.json"
    wallet_path.write_text(
        """
{
  "version": 1,
  "entries": [
    {
      "mint": "http://clear.example",
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
            "clear-lab",
            "--wallet",
            str(wallet_path),
            "withdraw",
            "5",
            "--memo",
            "send",
        ],
    )

    assert lab_cli.main() == 0
    output = capsys.readouterr().out

    assert '"token": "cashuA' in output
    assert '"amount": 5' in output
    assert '"entries": []' in wallet_path.read_text(encoding="utf-8")


def test_lab_cli_send_delivers_then_removes_from_local_wallet(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    wallet_path = tmp_path / "clear-lab-wallet.json"
    wallet_path.write_text(
        """
{
  "version": 1,
  "entries": [
    {
      "mint": "http://clear.example",
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
        lab_cli,
        "request_json",
        lambda mint_url, method, path, payload=None, *, token=None: {
            "currency": {"unit": "cmu-0011223344556677"}
        },
    )
    monkeypatch.setattr(
        lab_cli,
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
        lab_cli,
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
    monkeypatch.delenv("CLEAR_LAB_NSEC", raising=False)
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-lab",
            "--mint-url",
            "http://clear.example",
            "--wallet",
            str(wallet_path),
            "send",
            "5",
            "alice@example.com",
            "--memo",
            "send",
        ],
    )

    assert lab_cli.main() == 0
    output = capsys.readouterr().out

    assert '"status": "OK"' in output
    assert '"sender_ephemeral": true' in output
    assert '"entries": []' in wallet_path.read_text(encoding="utf-8")


def test_lab_cli_send_preserves_wallet_when_delivery_fails(
    tmp_path,
    monkeypatch,
) -> None:
    wallet_path = tmp_path / "clear-lab-wallet.json"
    original = """
{
  "version": 1,
  "entries": [
    {
      "mint": "http://clear.example",
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
        lab_cli,
        "request_json",
        lambda mint_url, method, path, payload=None, *, token=None: {
            "currency": {"unit": "cmu-0011223344556677"}
        },
    )
    monkeypatch.setattr(
        lab_cli,
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
        raise lab_cli.DeliveryError("delivery failed")

    monkeypatch.setattr(lab_cli, "deliver_clear_token", fail_delivery)
    monkeypatch.delenv("CLEAR_LAB_NSEC", raising=False)
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-lab",
            "--mint-url",
            "http://clear.example",
            "--wallet",
            str(wallet_path),
            "send",
            "5",
            "alice@example.com",
        ],
    )

    assert lab_cli.main() == 1
    assert wallet_path.read_text(encoding="utf-8") == original


def test_lab_cli_send_swaps_larger_proof_for_change(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    wallet_path = tmp_path / "clear-lab-wallet.json"
    wallet_path.write_text(
        """
{
  "version": 1,
  "entries": [
    {
      "mint": "http://clear.example",
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
        lab_cli,
        "request_json",
        lambda mint_url, method, path, payload=None, *, token=None: {
            "currency": {"unit": "cmu-0011223344556677"}
        },
    )
    monkeypatch.setattr(
        lab_cli,
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
        lab_cli,
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
        lab_cli,
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
            "clear-lab",
            "--mint-url",
            "http://clear.example",
            "--wallet",
            str(wallet_path),
            "send",
            "25",
            "alice@example.com",
            "--memo",
            "send",
        ],
    )

    assert lab_cli.main() == 0
    output = capsys.readouterr().out
    wallet = json.loads(wallet_path.read_text(encoding="utf-8"))
    remaining_amount = sum(
        proof["amount"]
        for entry in wallet["entries"]
        for proof in entry["proofs"]
    )

    assert '"amount": 25' in output
    assert remaining_amount == 7


def test_lab_cli_redeem_reads_token_from_stdin(monkeypatch, capsys) -> None:
    redeemed = {
        "mint": "http://clear.example",
        "unit": "cmu-0011223344556677",
        "amount": 21,
        "status": "RETIRED",
        "memo": None,
    }
    monkeypatch.setenv("CLEAR_OPERATOR_TOKEN", "operator-token")
    monkeypatch.setattr("sys.stdin.read", lambda: "cashuAtoken")
    monkeypatch.setattr(
        lab_cli,
        "redeem_token",
        lambda mint_url, operator_token, token, *, memo=None: redeemed,
    )
    monkeypatch.setattr(
        "sys.argv",
        ["clear-lab", "--mint-url", "http://clear.example", "redeem"],
    )

    assert lab_cli.main() == 0
    output = capsys.readouterr().out

    assert '"status": "RETIRED"' in output


def test_lab_cli_summary_calls_operator_endpoint(monkeypatch, capsys) -> None:
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

    monkeypatch.setattr(lab_cli, "request_json", fake_request_json)
    monkeypatch.setattr(
        "sys.argv",
        ["clear-lab", "--mint-url", "http://clear.example/", "summary"],
    )

    assert lab_cli.main() == 0
    output = capsys.readouterr().out

    assert '"outstanding": 13' in output
    assert calls == [
        (
            "http://clear.example",
            "GET",
            "/v1/operator/summary",
            None,
            "operator-token",
        )
    ]


def test_lab_cli_info_combines_cmu_metadata_and_circulation(
    monkeypatch,
    capsys,
) -> None:
    calls = []
    monkeypatch.setenv("CLEAR_OPERATOR_TOKEN", "operator-token")

    def fake_request_json(mint_url, method, path, payload=None, *, token=None):
        calls.append((mint_url, method, path, payload, token))
        if path == "/v1/info":
            return {
                "name": "Clear",
                "version": "0.1.0",
                "description": "Example Credits issued as Clear ecash",
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
                    "mode": "lab",
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

    monkeypatch.setattr(lab_cli, "request_json", fake_request_json)
    monkeypatch.setattr(
        "sys.argv",
        ["clear-lab", "--mint-url", "http://clear.example/", "info"],
    )

    assert lab_cli.main() == 0
    output = capsys.readouterr().out

    assert '"unit": "cmu-0011223344556677"' in output
    assert '"friendly_alias": "Example Credits (cmu-0011223344556677)"' in output
    assert '"friendly_unit_alias": "smiles"' in output
    assert '"root_authority_npub": "npub1root"' in output
    assert '"issued": 34' in output
    assert '"retired": 13' in output
    assert '"outstanding": 21' in output
    assert calls == [
        ("http://clear.example", "GET", "/v1/info", None, None),
        (
            "http://clear.example",
            "GET",
            "/v1/operator/summary",
            None,
            "operator-token",
        ),
    ]
