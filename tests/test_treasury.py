from __future__ import annotations

import pytest

from clear import treasury
from clear.tokens import encode_token_v3


def test_split_amount_into_supported_denominations() -> None:
    assert treasury.split_amount(1) == [1]
    assert treasury.split_amount(13) == [8, 4, 1]
    assert treasury.split_amount(21) == [16, 4, 1]


def test_split_amount_rejects_non_positive_values() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        treasury.split_amount(0)


def test_issue_token_authorizes_quote_and_unblinds_signatures(monkeypatch) -> None:
    calls = []

    def fake_request_json(mint_url, method, path, payload=None, *, token=None):
        calls.append((method, path, payload, token))
        if path == "/v1/info":
            return {"currency": {"unit": "cmu-0011223344556677"}}
        if path == "/v1/keys":
            return {
                "keysets": [
                    {
                        "id": "keyset-id",
                        "keys": {"1": "pub1", "4": "pub4", "8": "pub8"},
                    }
                ]
            }
        if path == "/v1/mint/quote/clear":
            return {"quote": "quote-id"}
        if path == "/v1/operator/quotes/quote-id/authorize":
            return {"quote": "quote-id", "amount_paid": 13}
        if path == "/v1/mint/clear":
            return {
                "signatures": [
                    {"C_": "promise-8"},
                    {"C_": "promise-4"},
                    {"C_": "promise-1"},
                ]
            }
        raise AssertionError(path)

    class FakeOutput:
        def __init__(self, amount):
            self.amount = amount
            self.payload = {"amount": amount, "id": "keyset-id", "B_": f"B-{amount}"}

    monkeypatch.setattr(treasury, "request_json", fake_request_json)
    monkeypatch.setattr(
        treasury,
        "blind_output",
        lambda amount, keyset_id: FakeOutput(amount),
    )
    monkeypatch.setattr(
        treasury,
        "unblind_signature",
        lambda output, promise, mint_public_key: {
            "amount": output.amount,
            "id": output.payload["id"],
            "secret": f"secret-{output.amount}",
            "C": promise["C_"],
        },
    )

    issued = treasury.issue_token(
        "http://clear.example/",
        "operator-token",
        13,
        memo="test issuance",
    )

    assert issued["mint"] == "http://clear.example"
    assert issued["unit"] == "cmu-0011223344556677"
    assert issued["amount"] == 13
    assert issued["token"].startswith("cashuA")
    assert [proof["amount"] for proof in issued["proofs"]] == [8, 4, 1]
    assert calls[2] == (
        "POST",
        "/v1/mint/quote/clear",
        {"amount": 13, "unit": "cmu-0011223344556677", "memo": "test issuance"},
        None,
    )
    assert calls[3] == (
        "POST",
        "/v1/operator/quotes/quote-id/authorize",
        None,
        "operator-token",
    )


def test_redeem_token_decodes_proofs_and_retires(monkeypatch) -> None:
    calls = []
    proofs = [
        {
            "amount": 8,
            "id": "keyset-id",
            "secret": "00" * 32,
            "C": "02" + "11" * 32,
        }
    ]
    token = encode_token_v3(
        mint="http://clear.example/",
        proofs=proofs,
        unit="cmu-0011223344556677",
        memo="issued token memo",
    )

    def fake_request_json(mint_url, method, path, payload=None, *, token=None):
        calls.append((mint_url, method, path, payload, token))
        return {"status": "RETIRED", "amount": 8, "unit": "cmu-0011223344556677"}

    monkeypatch.setattr(treasury, "request_json", fake_request_json)

    redeemed = treasury.redeem_token(
        "http://clear.example/",
        "operator-token",
        token,
        memo="program completed",
    )

    assert redeemed == {
        "mint": "http://clear.example",
        "unit": "cmu-0011223344556677",
        "amount": 8,
        "status": "RETIRED",
        "memo": "program completed",
    }
    assert calls == [
        (
            "http://clear.example",
            "POST",
            "/v1/operator/retire",
            {"inputs": proofs, "memo": "program completed"},
            "operator-token",
        )
    ]


def test_redeem_token_rejects_different_mint() -> None:
    token = encode_token_v3(
        mint="http://other.example",
        proofs=[
            {
                "amount": 1,
                "id": "keyset-id",
                "secret": "00" * 32,
                "C": "02" + "11" * 32,
            }
        ],
        unit="cmu-0011223344556677",
    )

    with pytest.raises(treasury.TreasuryError, match="not configured mint"):
        treasury.redeem_token("http://clear.example", "operator-token", token)
