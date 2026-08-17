from __future__ import annotations

from clear.tokens import decode_token_v3, encode_token_v3


def test_encode_cashu_token_v3() -> None:
    proofs = [
        {
            "amount": 8,
            "id": "01abcdef",
            "secret": "00" * 32,
            "C": "02" + "11" * 32,
        }
    ]

    token = encode_token_v3(
        mint="http://127.0.0.1:3339/",
        proofs=proofs,
        unit="cmu-0011223344556677",
        memo="test issuance",
    )

    assert token.startswith("cashuA")
    assert decode_token_v3(token) == {
        "token": [{"mint": "http://127.0.0.1:3339", "proofs": proofs}],
        "unit": "cmu-0011223344556677",
        "memo": "test issuance",
    }


def test_decode_cashu_token_v3_accepts_uri_prefix() -> None:
    token = encode_token_v3(
        mint="http://127.0.0.1:3339",
        proofs=[],
        unit="cmu-0011223344556677",
    )

    assert decode_token_v3(f"cashu:{token}")["unit"] == "cmu-0011223344556677"
