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
    currency_name: str = "Example Credits",
    root_authority_npub: str | None = None,
    currency_alias: str | None = None,
    currency_unit_alias: str | None = None,
    root_api_loopback_only: bool = False,
) -> Settings:
    return Settings(
        database_path=tmp_path / "clear.sqlite3",
        master_secret=master_secret,
        operator_token=OPERATOR_TOKEN,
        currency_name=currency_name,
        mint_url="https://clear.example",
        max_order=10,
        root_authority_npub=root_authority_npub,
        currency_alias=currency_alias,
        currency_unit_alias=currency_unit_alias,
        root_api_loopback_only=root_api_loopback_only,
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
    assert mint_info.json()["mint_url"] == "https://clear.example"
    assert info.json()["currency"]["display_unit"] == "CMU"
    currency = info.json()["currency"]
    assert currency["protocol_unit"] == f"cmu-{currency['keyset_fingerprint']}"
    assert keys.json()["keysets"][0]["unit"] == currency["protocol_unit"]
    assert keys.json()["keysets"][0]["id"].startswith("01")
    assert mint_info.json()["currency"] == {
        "name": "Example Credits",
        "display_unit": "CMU",
        "unit": currency["protocol_unit"],
        "keyset_fingerprint": currency["keyset_fingerprint"],
        "keyset_id": currency["keyset_id"],
        "friendly_alias": f"Example Credits ({currency['protocol_unit']})",
        "friendly_unit_alias": None,
        "friendly_alias_key": (
            f"example-credits:{currency['keyset_fingerprint']}"
        ),
        "identity_note": (
            "Suggested wallet label only; balances must bind to mint URL, "
            "unit, and keyset id."
        ),
    }
    assert info.json()["currency"]["friendly_alias"] == (
        f"Example Credits ({currency['protocol_unit']})"
    )
    assert info.json()["policy"] == {
        "mode": "root-bootstrap",
        "root_authority_npub": None,
        "enforced": False,
    }
    assert mint_info.json()["policy"] == info.json()["policy"]


def test_browser_homepage_is_friendly_and_keeps_json_api(tmp_path) -> None:
    configured = settings(
        tmp_path,
        currency_alias="Harbour Lab Credits",
        currency_unit_alias="smiles",
    )
    with TestClient(create_app(configured)) as client:
        homepage = client.get("/", headers={"Accept": "text/html"})
        information = client.get("/", headers={"Accept": "application/json"})

    assert homepage.status_code == 200
    assert homepage.headers["content-type"].startswith("text/html")
    assert "Harbour Lab Credits" in homepage.text
    assert "smiles" in homepage.text
    assert "https://clear.example" in homepage.text
    assert "Copy mint URL" in homepage.text
    assert "Organization-issued transferable units" in homepage.text
    assert information.json()["currency"]["friendly_alias"] == (
        "Harbour Lab Credits"
    )


def test_root_authority_npub_is_reported_as_policy_metadata(tmp_path) -> None:
    root_authority = "npub1clearrootauthority000000000000000000000000000000"
    configured = settings(tmp_path, root_authority_npub=root_authority)
    with TestClient(create_app(configured)) as client:
        info = client.get("/v1/info")

    assert info.json()["policy"] == {
        "mode": "root-bootstrap",
        "root_authority_npub": root_authority,
        "enforced": False,
    }


def test_operator_api_requires_loopback_client(tmp_path) -> None:
    configured = settings(tmp_path, root_api_loopback_only=True)
    app = create_app(configured)
    headers = {"Authorization": f"Bearer {OPERATOR_TOKEN}"}

    with TestClient(app, client=("203.0.113.10", 50000)) as remote_client:
        rejected = remote_client.get("/v1/operator/summary", headers=headers)

    with TestClient(app, client=("127.0.0.1", 50000)) as local_client:
        accepted = local_client.get("/v1/operator/summary", headers=headers)

    assert rejected.status_code == 403
    assert rejected.json() == {"detail": "operator API requires loopback access"}
    assert accepted.status_code == 200


def test_currency_aliases_can_be_configured_for_wallet_display(tmp_path) -> None:
    configured = settings(
        tmp_path,
        currency_alias="Harbour Lab Credits",
        currency_unit_alias="smiles",
    )
    with TestClient(create_app(configured)) as client:
        info = client.get("/v1/info")

    currency = info.json()["currency"]
    assert currency["friendly_alias"] == "Harbour Lab Credits"
    assert currency["friendly_unit_alias"] == "smiles"
    assert currency["friendly_alias_key"] == (
        f"harbour-lab-credits:{currency['keyset_fingerprint']}"
    )


def test_root_authority_npub_changes_the_active_keyset(tmp_path) -> None:
    no_root = create_app(settings(tmp_path / "no-root"))
    first_root = create_app(
        settings(tmp_path / "first-root", root_authority_npub="npub1firstroot")
    )
    second_root = create_app(
        settings(tmp_path / "second-root", root_authority_npub="npub1secondroot")
    )

    assert no_root.state.keyset.unit != first_root.state.keyset.unit
    assert first_root.state.keyset.unit != second_root.state.keyset.unit
    assert first_root.state.keyset.id != second_root.state.keyset.id


def test_missing_root_authority_preserves_legacy_keyset_derivation() -> None:
    legacy = Keyset(MASTER_SECRET, max_order=10)
    explicit_none = Keyset(MASTER_SECRET, max_order=10, root_authority_npub=None)

    assert explicit_none.unit == legacy.unit
    assert explicit_none.id == legacy.id
    assert explicit_none.public_keys == legacy.public_keys


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
    assert summary.json()["circulating"] == 4
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
    second = create_app(
        settings(tmp_path / "second", currency_name="Friendly Credits")
    )

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


def test_settings_load_from_working_directory_env_file(tmp_path, monkeypatch) -> None:
    dotenv_path = tmp_path / ".env"
    database_path = tmp_path / "dotenv.sqlite3"
    dotenv_path.write_text(
        "\n".join(
            [
                f"CLEAR_MASTER_SECRET={MASTER_SECRET}",
                f"CLEAR_OPERATOR_TOKEN={OPERATOR_TOKEN}",
                f"CLEAR_DATABASE={database_path}",
                "CLEAR_CURRENCY_NAME=Dotenv Credits",
                "CLEAR_ROOT_AUTHORITY_NPUB=npub1dotenvrootauthority",
                "CLEAR_CURRENCY_ALIAS=Dotenv Alias",
                "CLEAR_CURRENCY_UNIT_ALIAS=beans",
            ]
        )
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CLEAR_MASTER_SECRET", raising=False)
    monkeypatch.delenv("CLEAR_OPERATOR_TOKEN", raising=False)
    monkeypatch.delenv("CLEAR_DATABASE", raising=False)
    monkeypatch.delenv("CLEAR_CURRENCY_NAME", raising=False)
    monkeypatch.delenv("CLEAR_ROOT_AUTHORITY_NPUB", raising=False)
    monkeypatch.delenv("CLEAR_CURRENCY_ALIAS", raising=False)
    monkeypatch.delenv("CLEAR_CURRENCY_UNIT_ALIAS", raising=False)

    settings = Settings.from_env()

    assert settings.master_secret == MASTER_SECRET
    assert settings.operator_token == OPERATOR_TOKEN
    assert settings.database_path == database_path
    assert settings.currency_name == "Dotenv Credits"
    assert settings.root_authority_npub == "npub1dotenvrootauthority"
    assert settings.currency_alias == "Dotenv Alias"
    assert settings.currency_unit_alias == "beans"


def test_environment_values_override_dotenv_file(tmp_path, monkeypatch) -> None:
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                f"CLEAR_MASTER_SECRET={MASTER_SECRET}",
                f"CLEAR_OPERATOR_TOKEN={OPERATOR_TOKEN}",
                "CLEAR_CURRENCY_NAME=Dotenv Credits",
            ]
        )
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLEAR_MASTER_SECRET", "22" * 32)
    monkeypatch.setenv("CLEAR_OPERATOR_TOKEN", "environment-token-is-long")
    monkeypatch.setenv("CLEAR_CURRENCY_NAME", "Environment Credits")

    settings = Settings.from_env()

    assert settings.master_secret == "22" * 32
    assert settings.operator_token == "environment-token-is-long"
    assert settings.currency_name == "Environment Credits"
