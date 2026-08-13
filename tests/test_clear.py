from __future__ import annotations

import pytest
from coincurve import PrivateKey, PublicKey
from fastapi.testclient import TestClient

from clear.config import Settings
from clear.crypto import CURVE_ORDER, Keyset, hash_to_curve
from clear.main import create_app

MASTER_SECRET = "11" * 32
OPERATOR_TOKEN = "operator-token-that-is-long-enough"


def settings(
    tmp_path,
    *,
    master_secret: str = MASTER_SECRET,
    currency_name: str = "Example Points",
) -> Settings:
    return Settings(
        database_path=tmp_path / "clear.sqlite3",
        master_secret=master_secret,
        operator_token=OPERATOR_TOKEN,
        currency_name=currency_name,
        mint_url="https://clear.example",
        max_order=10,
    )


def blinded_output(
    keyset: Keyset, amount: int, secret: str, r: int
) -> tuple[dict, int]:
    y = hash_to_curve(secret)
    r_key = PrivateKey(r.to_bytes(32, "big")).public_key
    blinded = PublicKey.combine_keys([y, r_key]).format(compressed=True).hex()
    return {"amount": amount, "id": keyset.id, "B_": blinded}, r


def unblind(
    keyset: Keyset,
    amount: int,
    secret: str,
    r: int,
    promise: dict,
) -> dict:
    promise_point = PublicKey(bytes.fromhex(promise["C_"]))
    mint_key = PublicKey(bytes.fromhex(keyset.public_keys[amount]))
    negative_r = (CURVE_ORDER - r).to_bytes(32, "big")
    signature = PublicKey.combine_keys(
        [promise_point, mint_key.multiply(negative_r)]
    ).format(compressed=True)
    return {
        "amount": amount,
        "id": keyset.id,
        "secret": secret,
        "C": signature.hex(),
    }


def issue_proof(client: TestClient, keyset: Keyset, amount: int = 8) -> dict:
    quote = client.post(
        "/v1/mint/quote/clear",
        json={"amount": amount, "unit": keyset.unit},
    ).json()
    response = client.post(f"/v1/operator/quotes/{quote['quote']}/authorize")
    assert response.status_code == 401
    authorized = client.post(
        f"/v1/operator/quotes/{quote['quote']}/authorize",
        headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
    )
    assert authorized.status_code == 200
    output, r = blinded_output(keyset, amount, "first-secret", 17)
    minted = client.post(
        "/v1/mint/clear",
        json={"quote": quote["quote"], "outputs": [output]},
    )
    assert minted.status_code == 200
    return unblind(keyset, amount, "first-secret", r, minted.json()["signatures"][0])


def test_information_health_and_unique_currency(tmp_path) -> None:
    configured = settings(tmp_path)
    with TestClient(create_app(configured)) as client:
        info = client.get("/")
        health = client.get("/health")
        keys = client.get("/v1/keys")
        mint_info = client.get("/v1/info")

    assert health.json() == {"status": "ok"}
    assert info.json()["currency"]["display_unit"] == "pts"
    currency = info.json()["currency"]
    assert currency["protocol_unit"] == f"pts.{currency['keyset_fingerprint']}"
    assert keys.json()["keysets"][0]["unit"] == currency["protocol_unit"]
    assert keys.json()["keysets"][0]["id"].startswith("01")
    assert mint_info.json()["currency"] == {
        "name": "Example Points",
        "display_unit": "pts",
        "unit": currency["protocol_unit"],
        "keyset_fingerprint": currency["keyset_fingerprint"],
        "keyset_id": currency["keyset_id"],
    }


def test_authorized_issuance_is_idempotent(tmp_path) -> None:
    configured = settings(tmp_path)
    app = create_app(configured)
    keyset = app.state.keyset
    with TestClient(app) as client:
        quote = client.post(
            "/v1/mint/quote/clear",
            json={"amount": 8, "unit": keyset.unit},
        ).json()
        client.post(
            f"/v1/operator/quotes/{quote['quote']}/authorize",
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        output, _ = blinded_output(keyset, 8, "idempotent-secret", 19)
        request = {"quote": quote["quote"], "outputs": [output]}
        first = client.post("/v1/mint/clear", json=request)
        second = client.post("/v1/mint/clear", json=request)
        checked = client.get(f"/v1/mint/quote/clear/{quote['quote']}")

    assert first.status_code == 200
    assert second.json() == first.json()
    assert checked.json()["amount_issued"] == 8


def test_blinded_output_cannot_be_issued_by_two_quotes(tmp_path) -> None:
    configured = settings(tmp_path)
    app = create_app(configured)
    keyset = app.state.keyset
    output, _ = blinded_output(keyset, 8, "reused-output", 37)
    with TestClient(app) as client:
        quotes = []
        for _ in range(2):
            quote = client.post(
                "/v1/mint/quote/clear",
                json={"amount": 8, "unit": keyset.unit},
            ).json()
            client.post(
                f"/v1/operator/quotes/{quote['quote']}/authorize",
                headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
            )
            quotes.append(quote)

        first = client.post(
            "/v1/mint/clear",
            json={"quote": quotes[0]["quote"], "outputs": [output]},
        )
        second = client.post(
            "/v1/mint/clear",
            json={"quote": quotes[1]["quote"], "outputs": [output]},
        )

    assert first.status_code == 200
    assert second.status_code == 400
    assert "already been signed" in second.json()["detail"]


def test_issue_swap_check_state_and_retire(tmp_path) -> None:
    configured = settings(tmp_path)
    app = create_app(configured)
    keyset = app.state.keyset
    with TestClient(app) as client:
        original = issue_proof(client, keyset)
        original_y = hash_to_curve(original["secret"]).format(compressed=True).hex()
        output_one, r_one = blinded_output(keyset, 4, "swap-secret-one", 23)
        output_two, r_two = blinded_output(keyset, 4, "swap-secret-two", 29)
        swapped = client.post(
            "/v1/swap",
            json={"inputs": [original], "outputs": [output_one, output_two]},
        )
        assert swapped.status_code == 200
        promises = swapped.json()["signatures"]
        proof_one = unblind(keyset, 4, "swap-secret-one", r_one, promises[0])
        proof_two = unblind(keyset, 4, "swap-secret-two", r_two, promises[1])

        state = client.post("/v1/checkstate", json={"Ys": [original_y]})
        unauthorized = client.post("/v1/operator/retire", json={"inputs": [proof_one]})
        retired = client.post(
            "/v1/operator/retire",
            json={"inputs": [proof_one], "memo": "program completed"},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        summary = client.get(
            "/v1/operator/summary",
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        still_unspent_y = (
            hash_to_curve(proof_two["secret"]).format(compressed=True).hex()
        )
        still_unspent = client.post("/v1/checkstate", json={"Ys": [still_unspent_y]})

    assert state.json()["states"][0]["state"] == "SPENT"
    assert unauthorized.status_code == 401
    assert retired.json()["amount"] == 4
    assert summary.json()["issued"] == 8
    assert summary.json()["retired"] == 4
    assert summary.json()["outstanding"] == 4
    assert still_unspent.json()["states"][0]["state"] == "UNSPENT"


def test_proofs_from_different_clear_currency_are_rejected(tmp_path) -> None:
    first_settings = settings(tmp_path / "first")
    first_app = create_app(first_settings)
    with TestClient(first_app) as first_client:
        proof = issue_proof(first_client, first_app.state.keyset)

    second_settings = settings(tmp_path / "second", master_secret="22" * 32)
    second_app = create_app(second_settings)
    with TestClient(second_app) as second_client:
        output, _ = blinded_output(second_app.state.keyset, 8, "other-output", 31)
        response = second_client.post(
            "/v1/swap", json={"inputs": [proof], "outputs": [output]}
        )

    assert response.status_code == 400
    assert "another Clear currency" in response.json()["detail"]
    assert first_app.state.keyset.unit != second_app.state.keyset.unit


def test_friendly_name_does_not_change_currency_identity(tmp_path) -> None:
    first = create_app(settings(tmp_path / "first", currency_name="Harbour Credits"))
    second = create_app(settings(tmp_path / "second", currency_name="Friendly Points"))

    assert first.state.keyset.unit == second.state.keyset.unit
    assert first.state.keyset.id == second.state.keyset.id


def test_database_is_bound_to_one_keyset_currency(tmp_path) -> None:
    database_settings = settings(tmp_path)
    with TestClient(create_app(database_settings)):
        pass

    changed_secret = settings(tmp_path, master_secret="22" * 32)
    with pytest.raises(RuntimeError, match="does not match"):
        with TestClient(create_app(changed_secret)):
            pass
