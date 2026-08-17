from __future__ import annotations

import pytest

from clear import treasury
from clear.tokens import decode_token_v3, encode_token_v3


def test_split_amount_into_supported_denominations() -> None:
    assert treasury.split_amount(1) == [1]
    assert treasury.split_amount(13) == [8, 4, 1]
    assert treasury.split_amount(21) == [16, 4, 1]


def test_split_amount_rejects_non_positive_values() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        treasury.split_amount(0)


def test_issue_units_authorizes_quote_and_unblinds_signatures(monkeypatch) -> None:
    calls = []

    def fake_request_json(mint_url, method, path, payload=None, *, token=None):
        calls.append((method, path, payload, token))
        if path == "/v1/info":
            return {
                "mint_url": "https://clear.example",
                "currency": {"unit": "cmu-0011223344556677"},
            }
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

    issued = treasury.issue_units(
        "http://127.0.0.1:3339/",
        "operator-token",
        13,
        memo="test issuance",
    )

    assert issued["mint"] == "https://clear.example"
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


def test_swap_uses_internal_api_but_preserves_public_mint_url(monkeypatch) -> None:
    calls = []

    def fake_request_json(mint_url, method, path, payload=None, *, token=None):
        calls.append((mint_url, method, path))
        if path == "/v1/info":
            return {"mint_url": "https://clear.example"}
        if path == "/v1/keys":
            return {
                "keysets": [
                    {"id": "keyset-id", "keys": {"1": "pub1"}}
                ]
            }
        if path == "/v1/swap":
            return {"signatures": [{"C_": "send"}, {"C_": "change"}]}
        raise AssertionError(path)

    class FakeOutput:
        def __init__(self, amount):
            self.amount = amount
            self.payload = {"amount": amount, "id": "keyset-id", "B_": "B"}

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
            "secret": promise["C_"],
            "C": promise["C_"],
        },
    )

    swapped = treasury.swap_token_for_amount(
        "http://127.0.0.1:3339",
        [{"amount": 2, "id": "keyset-id"}],
        1,
        unit="cmu-0011223344556677",
    )

    assert swapped["mint"] == "https://clear.example"
    assert decode_token_v3(swapped["token"])["token"][0]["mint"] == (
        "https://clear.example"
    )
    assert calls == [
        ("http://127.0.0.1:3339", "GET", "/v1/info"),
        ("http://127.0.0.1:3339", "GET", "/v1/keys"),
        ("http://127.0.0.1:3339", "POST", "/v1/swap"),
    ]


def test_retire_token_decodes_proofs_and_retires(monkeypatch) -> None:
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
        if path == "/v1/info":
            return {"mint_url": "http://clear.example"}
        return {"status": "RETIRED", "amount": 8, "unit": "cmu-0011223344556677"}

    monkeypatch.setattr(treasury, "request_json", fake_request_json)

    redeemed = treasury.retire_token(
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
        ("http://clear.example", "GET", "/v1/info", None, None),
        (
            "http://clear.example",
            "POST",
            "/v1/operator/retire",
            {"inputs": proofs, "memo": "program completed"},
            "operator-token",
        )
    ]


def test_retire_token_rejects_different_mint(monkeypatch) -> None:
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

    monkeypatch.setattr(
        treasury,
        "request_json",
        lambda mint_url, method, path, payload=None, *, token=None: {
            "mint_url": "http://clear.example"
        },
    )

    with pytest.raises(treasury.TreasuryError, match="not configured mint"):
        treasury.retire_token("http://clear.example", "operator-token", token)


def test_retire_proofs_validates_unit_and_calls_operator_endpoint(monkeypatch) -> None:
    calls = []
    proofs = [
        {
            "amount": 8,
            "id": "keyset-id",
            "secret": "00" * 32,
            "C": "02" + "11" * 32,
        }
    ]

    def fake_request_json(mint_url, method, path, payload=None, *, token=None):
        calls.append((mint_url, method, path, payload, token))
        if path == "/v1/info":
            return {
                "mint_url": "https://clear.example",
                "currency": {"unit": "cmu-test"},
            }
        return {"status": "RETIRED", "amount": 8, "unit": "cmu-test"}

    monkeypatch.setattr(treasury, "request_json", fake_request_json)

    retired = treasury.retire_proofs(
        "http://127.0.0.1:3339",
        "operator-token",
        proofs,
        unit="cmu-test",
        memo="expired",
    )

    assert retired["mint"] == "https://clear.example"
    assert retired["unit"] == "cmu-test"
    assert retired["amount"] == 8
    assert calls[-1] == (
        "http://127.0.0.1:3339",
        "POST",
        "/v1/operator/retire",
        {"inputs": proofs, "memo": "expired"},
        "operator-token",
    )


def test_retire_proofs_rejects_wrong_cmu(monkeypatch) -> None:
    monkeypatch.setattr(
        treasury,
        "request_json",
        lambda mint_url, method, path, payload=None, *, token=None: {
            "mint_url": "https://clear.example",
            "currency": {"unit": "cmu-test"},
        },
    )

    with pytest.raises(treasury.TreasuryError, match="not configured unit"):
        treasury.retire_proofs(
            "http://127.0.0.1:3339",
            "operator-token",
            [
                {
                    "amount": 1,
                    "id": "keyset-id",
                    "secret": "secret",
                    "C": "signature",
                }
            ],
            unit="cmu-other",
        )
