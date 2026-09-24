from __future__ import annotations

import base64

import cbor2
import pytest

from clear.tokens import (
    MAX_TOKEN_LENGTH,
    decode_token,
    decode_token_v3,
    encode_token_v3,
    encode_token_v4,
)


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


# Published NUT-00 TokenV4 example (two keysets, three proofs).
# https://github.com/cashubtc/nuts/blob/main/00.md#v4-tokens
NUT00_TOKEN = (
    "cashuBo2F0gqJhaUgA_9SLj17PgGFwgaNhYQFhc3hAYWNjMTI0MzVlN2I4NDg0YzNjZjE4"
    "NTAxNDkyMThhZjkwZjcxNmE1MmJmNGE1ZWQzNDdlNDhlY2MxM2Y3NzM4OGFjWCECRFODGd5I"
    "XVW-07KaZCvuWHk3WrnnpiDhHki6SCQh88-iYWlIAK0mjE0fWCZhcIKjYWECYXN4QDEzMjNk"
    "M2Q0NzA3YTU4YWQyZTIzYWRhNGU5ZjFmNDlmNWE1YjRhYzdiNzA4ZWIwZDYxZjczOGY0ODMw"
    "N2U4ZWVhY1ghAjRWqhENhLSsdHrr2Cw7AFrKUL9Ffr1XN6RBT6w659lNo2FhAWFzeEA1NmJj"
    "YmNiYjdjYzY0MDZiM2ZhNWQ1N2QyMTc0ZjRlZmY4YjQ0MDJiMTc2OTI2ZDNhNTdkM2MzZGNi"
    "YjU5ZDU3YWNYIQJzEpxXGeWZN5qXSmJjY8MzxWyvwObQGr5G1YCCgHicY2FtdWh0dHA6Ly9s"
    "b2NhbGhvc3Q6MzMzOGF1Y3NhdA"
)


def wire_token(payload):
    return "cashuB" + base64.urlsafe_b64encode(cbor2.dumps(payload)).decode()


def wire_payload():
    return {
        "m": "https://clear.example",
        "u": "cmu-0011223344556677",
        "t": [
            {
                "i": bytes.fromhex("01" + "ab" * 32),
                "p": [
                    {
                        "a": 8,
                        "s": "bearer-secret",
                        "c": bytes.fromhex("02" + "11" * 32),
                    }
                ],
            }
        ],
    }


@pytest.mark.parametrize("uri", ["", "cashu:"])
@pytest.mark.parametrize("padding", [False, True])
def test_decode_official_v4_vector(uri, padding):
    token = NUT00_TOKEN
    if padding:
        token += "=" * (-len(token[6:]) % 4)
    result = decode_token(uri + token)
    assert result["unit"] == "sat"
    entry = result["token"][0]
    assert entry["mint"] == "http://localhost:3338"
    assert [p["amount"] for p in entry["proofs"]] == [1, 2, 1]
    assert [p["id"] for p in entry["proofs"]] == [
        "00ffd48b8f5ecf80",
        "00ad268c4d1f5826",
        "00ad268c4d1f5826",
    ]
    assert entry["proofs"][0]["C"] == (
        "0244538319de485d55bed3b29a642bee5879375ab9e7a620e11e48ba482421f3cf"
    )


@pytest.mark.parametrize("encoder", [encode_token_v3, encode_token_v4])
def test_token_formats_preserve_cmu_and_optional_proof_fields(encoder):
    proofs = [
        {
            "id": "01" + "ab" * 32,
            "amount": 8,
            "secret": "秘密",
            "C": "02" + "11" * 32,
            "dleq": {"e": "00" * 32, "s": "11" * 32, "r": "22" * 32},
            "witness": '{"signatures":[]}',
        }
    ]
    token = encoder(
        mint="https://clear.example/",
        proofs=proofs,
        unit="cmu-0011223344556677",
        memo="Transfer café",
    )
    assert decode_token(token) == {
        "token": [{"mint": "https://clear.example", "proofs": proofs}],
        "unit": "cmu-0011223344556677",
        "memo": "Transfer café",
    }
    if encoder is encode_token_v4:
        wire = cbor2.loads(
            base64.urlsafe_b64decode(token[6:] + "=" * (-len(token[6:]) % 4))
        )
        assert wire["t"][0]["i"] == bytes.fromhex(proofs[0]["id"])
        assert wire["t"][0]["p"][0]["c"] == bytes.fromhex(proofs[0]["C"])


def test_v4_groups_proofs_by_keyset():
    decoded = decode_token(NUT00_TOKEN)
    entry = decoded["token"][0]
    token = encode_token_v4(mint=entry["mint"], proofs=entry["proofs"], unit="sat")
    assert decode_token(token) == decoded


def test_v4_ignores_unknown_fields():
    payload = wire_payload()
    payload["future"] = "extension"
    payload["t"][0]["future"] = 1
    payload["t"][0]["p"][0]["future"] = True
    assert decode_token(wire_token(payload)) == decode_token(wire_token(wire_payload()))


@pytest.mark.parametrize("bad", [None, {}, [], True, -1, 0, 1.5, 2**64])
def test_v4_rejects_invalid_amount(bad):
    payload = wire_payload()
    payload["t"][0]["p"][0]["a"] = bad
    with pytest.raises(ValueError):
        decode_token(wire_token(payload))


@pytest.mark.parametrize(
    "bad",
    [
        "cashuB",
        "cashuB!",
        "cashuBgA",
        "cashuB_w",
        "cashuCabc",
        "cashuB" + "A" * MAX_TOKEN_LENGTH,
    ],
)
def test_rejects_malformed_tokens(bad):
    with pytest.raises(ValueError):
        decode_token(bad)


def test_v4_rejects_trailing_cbor():
    raw = cbor2.dumps(wire_payload()) + cbor2.dumps({})
    with pytest.raises(ValueError):
        decode_token("cashuB" + base64.urlsafe_b64encode(raw).decode())


@pytest.mark.parametrize("field,value", [("i", "01abcd"), ("p", []), ("p", {})])
def test_v4_rejects_malformed_keyset_groups(field, value):
    payload = wire_payload()
    payload["t"][0][field] = value
    with pytest.raises(ValueError):
        decode_token(wire_token(payload))


def test_v4_short_keysets_require_resolution():
    payload = wire_payload()
    full_id = payload["t"][0]["i"].hex()
    payload["t"][0]["i"] = bytes.fromhex(full_id[:16])
    token = wire_token(payload)
    with pytest.raises(ValueError):
        decode_token(token)

    def resolve(mint, short_id):
        assert mint == "https://clear.example"
        assert short_id == full_id[:16]
        return full_id

    assert (
        decode_token(token, resolve_keyset=resolve)["token"][0]["proofs"][0]["id"]
        == full_id
    )
    with pytest.raises(ValueError):
        decode_token(token, resolve_keyset=lambda *_: "01" + "ff" * 32)


@pytest.mark.parametrize("matches", [0, 1, 2])
def test_retirement_resolves_short_ids_only_at_configured_mint(monkeypatch, matches):
    from clear import treasury

    payload = wire_payload()
    full_id = payload["t"][0]["i"].hex()
    payload["t"][0]["i"] = bytes.fromhex(full_id[:16])
    ids = [full_id, full_id[:16] + "cd" * 25][:matches]
    calls = []

    def request(mint, method, path, body=None, *, token=None):
        assert mint == "http://127.0.0.1:3339"
        calls.append(path)
        if path == "/v1/info":
            return {"mint_url": payload["m"], "currency": {"unit": payload["u"]}}
        if path == "/v1/keysets":
            return {"keysets": [{"id": keyset} for keyset in ids]}
        assert path == "/v1/operator/retire"
        assert body["inputs"][0]["id"] == full_id
        return {"status": "RETIRED", "amount": 8, "unit": payload["u"]}

    monkeypatch.setattr(treasury, "request_json", request)
    if matches == 1:
        assert (
            treasury.retire_token(
                "http://127.0.0.1:3339",
                "operator-token",
                wire_token(payload),
            )["amount"]
            == 8
        )
    else:
        with pytest.raises((ValueError, treasury.TreasuryError)):
            treasury.retire_token(
                "http://127.0.0.1:3339",
                "operator-token",
                wire_token(payload),
            )
        assert "/v1/operator/retire" not in calls


def test_short_id_foreign_mint_does_not_trigger_lookup(monkeypatch):
    from clear import treasury

    payload = wire_payload()
    payload["m"] = "https://untrusted.example"
    payload["t"][0]["i"] = payload["t"][0]["i"][:8]

    def request(mint, method, path, body=None, *, token=None):
        assert mint == "https://clear.example"
        assert path == "/v1/info"
        return {"mint_url": "https://clear.example"}

    monkeypatch.setattr(treasury, "request_json", request)
    with pytest.raises((ValueError, treasury.TreasuryError)):
        treasury.retire_token(
            "https://clear.example",
            "operator-token",
            wire_token(payload),
        )
