from __future__ import annotations

from clear.root_wallet import deposit_issue, export_token, load_wallet, wallet_summary
from clear.tokens import decode_token_v3


def issued(
    amounts: list[int],
    *,
    unit: str = "cmu-0011223344556677",
    keyset_id: str = "keyset-id",
) -> dict:
    return {
        "mint": "http://clear.example",
        "unit": unit,
        "quote": "quote-id",
        "amount": sum(amounts),
        "memo": "root float",
        "proofs": [
            {
                "amount": amount,
                "id": keyset_id,
                "secret": f"{unit}-secret-{amount}",
                "C": f"signature-{amount}",
            }
            for amount in amounts
        ],
    }


def test_deposit_issue_creates_json_wallet(tmp_path) -> None:
    wallet_path = tmp_path / "data" / "clear-root-wallet.json"

    summary = deposit_issue(issued([8, 4, 1]), wallet_path)

    assert summary == {
        "wallet": str(wallet_path),
        "entries": 1,
        "balances": [
            {
                "mint": "http://clear.example",
                "unit": "cmu-0011223344556677",
                "amount": 13,
            }
        ],
    }
    assert wallet_summary(load_wallet(wallet_path), wallet_path) == summary


def test_export_token_from_root_wallet(tmp_path) -> None:
    wallet_path = tmp_path / "data" / "clear-root-wallet.json"
    deposit_issue(issued([8, 4, 1]), wallet_path)

    exported = export_token(13, wallet_path, memo="disburse")
    decoded = decode_token_v3(exported["token"])

    assert exported["amount"] == 13
    assert decoded["unit"] == "cmu-0011223344556677"
    assert decoded["memo"] == "disburse"
    assert [proof["amount"] for proof in decoded["token"][0]["proofs"]] == [8, 4, 1]
    assert wallet_summary(load_wallet(wallet_path), wallet_path)["balances"] == []


def test_export_token_finds_exact_subset(tmp_path) -> None:
    wallet_path = tmp_path / "data" / "clear-root-wallet.json"
    deposit_issue(issued([16, 8, 4, 1]), wallet_path)

    exported = export_token(13, wallet_path, memo="subset")
    decoded = decode_token_v3(exported["token"])

    assert [proof["amount"] for proof in decoded["token"][0]["proofs"]] == [8, 4, 1]
    assert wallet_summary(load_wallet(wallet_path), wallet_path)["balances"] == [
        {
            "mint": "http://clear.example",
            "unit": "cmu-0011223344556677",
            "amount": 16,
        }
    ]


def test_export_token_can_target_unit_in_mixed_wallet(tmp_path) -> None:
    wallet_path = tmp_path / "data" / "clear-root-wallet.json"
    deposit_issue(
        issued([8], unit="cmu-first", keyset_id="first-keyset"),
        wallet_path,
    )
    deposit_issue(
        issued([8], unit="cmu-second", keyset_id="second-keyset"),
        wallet_path,
    )

    exported = export_token(
        8,
        wallet_path,
        unit="cmu-second",
        memo="target second",
    )
    decoded = decode_token_v3(exported["token"])

    assert exported["unit"] == "cmu-second"
    assert decoded["unit"] == "cmu-second"
    assert decoded["token"][0]["proofs"][0]["id"] == "second-keyset"
    assert wallet_summary(load_wallet(wallet_path), wallet_path)["balances"] == [
        {
            "mint": "http://clear.example",
            "unit": "cmu-first",
            "amount": 8,
        }
    ]
