from __future__ import annotations

import pytest
from coincurve import PrivateKey, PublicKey
from fastapi.testclient import TestClient
from stroma import Keys

from clear.config import Settings
from clear.crypto import CURVE_ORDER, Keyset, hash_to_curve
from clear.main import create_app
from clear.store import ClearError
from clear.treasury_auth import (
    build_cmu_create_envelope,
    build_cmu_info_envelope,
    build_quote_authorize_envelope,
)

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


def issue_proof(
    client: TestClient,
    keyset: Keyset,
    amount: int = 8,
    secret: str = "first-secret",
) -> dict:
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
    output, r = blinded_output(keyset, amount, secret, 17)
    minted = client.post(
        "/v1/mint/clear",
        json={"quote": quote["quote"], "outputs": [output]},
    )
    assert minted.status_code == 200
    return unblind(keyset, amount, secret, r, minted.json()["signatures"][0])


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
        keysets = client.get("/v1/keysets")
        keys = client.get(f"/v1/keys/{info.json()['currency']['keyset_id']}")

    currency = info.json()["currency"]
    assert currency["friendly_alias"] == "Harbour Lab Credits"
    assert currency["friendly_unit_alias"] == "smiles"
    assert currency["friendly_alias_key"] == (
        f"harbour-lab-credits:{currency['keyset_fingerprint']}"
    )
    assert keysets.json()["keysets"][0]["friendly_alias"] == "Harbour Lab Credits"
    assert keysets.json()["keysets"][0]["friendly_name"] == "Harbour Lab Credits"
    assert keysets.json()["keysets"][0]["friendly_unit_alias"] == "smiles"
    assert keys.json()["keysets"][0]["friendly_alias"] == "Harbour Lab Credits"
    assert keys.json()["keysets"][0]["friendly_unit_alias"] == "smiles"


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


def test_operator_can_add_and_list_treasurers(tmp_path) -> None:
    configured = settings(tmp_path)
    npub = "npub1treasurer0000000000000000000000000000000000000000"
    with TestClient(create_app(configured)) as client:
        unauthorized = client.post("/v1/operator/treasurers", json={"npub": npub})
        added = client.post(
            "/v1/operator/treasurers",
            json={"npub": npub},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        repeated = client.post(
            "/v1/operator/treasurers",
            json={"npub": npub},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        listed = client.get(
            "/v1/operator/treasurers",
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )

    assert unauthorized.status_code == 401
    assert added.status_code == 200
    assert added.json()["npub"] == npub
    assert added.json()["status"] == "active"
    assert added.json()["created"] is True
    assert repeated.json()["created"] is False
    assert listed.json()["treasurers"] == [
        {
            "npub": npub,
            "status": "active",
            "added_at": added.json()["added_at"],
            "updated_at": added.json()["updated_at"],
            "removed_at": None,
        }
    ]


def test_operator_rejects_treasurer_nsec(tmp_path) -> None:
    configured = settings(tmp_path)
    with TestClient(create_app(configured)) as client:
        response = client.post(
            "/v1/operator/treasurers",
            json={"npub": "nsec1secretmustnotenterclear"},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )

    assert response.status_code == 400
    assert "nsec must never be submitted" in response.json()["detail"]


def test_operator_grant_requires_active_treasurer_and_is_single_use(tmp_path) -> None:
    configured = settings(tmp_path)
    app = create_app(configured)
    npub = "npub1treasurer0000000000000000000000000000000000000000"
    with TestClient(app) as client:
        missing = client.post(
            "/v1/operator/treasurer-grants",
            json={"npub": npub},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        client.post(
            "/v1/operator/treasurers",
            json={"npub": npub},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        granted = client.post(
            "/v1/operator/treasurer-grants",
            json={"npub": npub},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        duplicate_pending = client.post(
            "/v1/operator/treasurer-grants",
            json={"npub": npub},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        listed = client.get(
            "/v1/operator/treasurer-grants",
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )

    assert missing.status_code == 400
    assert "must be active" in missing.json()["detail"]
    assert granted.status_code == 200
    assert granted.json()["npub"] == npub
    assert granted.json()["scope"] == "keyset:create"
    assert granted.json()["max_uses"] == 1
    assert granted.json()["uses"] == 0
    assert granted.json()["status"] == "pending"
    assert granted.json()["keyset_id"] is None
    assert duplicate_pending.status_code == 400
    assert "unused grant" in duplicate_pending.json()["detail"]
    assert listed.json()["grants"] == [granted.json()]


def test_store_rejects_grant_after_treasurer_created_cmu(tmp_path) -> None:
    configured = settings(tmp_path)
    app = create_app(configured)
    npub = "npub1treasurer0000000000000000000000000000000000000000"
    with TestClient(app):
        app.state.store.add_treasurer(npub)
        grant = app.state.store.grant_treasurer(npub)
        consumed = app.state.store.consume_treasurer_grant(
            grant["id"], "keyset-created-by-grant"
        )
        with pytest.raises(ClearError, match="already created a CMU"):
            app.state.store.grant_treasurer(npub)

    assert consumed["status"] == "consumed"
    assert consumed["uses"] == 1
    assert consumed["keyset_id"] == "keyset-created-by-grant"


def test_operator_can_create_cmu_from_grant_and_discover_keyset(tmp_path) -> None:
    configured = settings(tmp_path)
    npub = "npub1treasurer0000000000000000000000000000000000000000"
    with TestClient(create_app(configured)) as client:
        legacy_keysets = client.get("/v1/keysets").json()["keysets"]
        client.post(
            "/v1/operator/treasurers",
            json={"npub": npub},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        grant = client.post(
            "/v1/operator/treasurer-grants",
            json={"npub": npub},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        ).json()
        created = client.post(
            "/v1/operator/cmus",
            json={
                "grant_id": grant["id"],
                "name": "Gym Guest Passes",
                "unit_alias": "passes",
            },
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        duplicate_create = client.post(
            "/v1/operator/cmus",
            json={"grant_id": grant["id"], "name": "Again"},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        duplicate_grant = client.post(
            "/v1/operator/treasurer-grants",
            json={"npub": npub},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        keysets = client.get("/v1/keysets").json()["keysets"]
        keys = client.get(f"/v1/keys/{created.json()['keyset_id']}")
        grants = client.get(
            "/v1/operator/treasurer-grants",
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        ).json()["grants"]

    assert created.status_code == 200
    cmu = created.json()
    assert cmu["unit"].startswith("cmu-")
    assert cmu["keyset_id"].startswith("01")
    assert cmu["friendly_name"] == "Gym Guest Passes"
    assert cmu["friendly_alias"] == "Gym Guest Passes"
    assert cmu["friendly_unit_alias"] == "passes"
    assert cmu["treasurer_npub"] == npub
    assert cmu["material_kind"] == "random-encrypted-v1"
    assert cmu["status"] == "active"
    assert duplicate_create.status_code == 400
    assert "not pending" in duplicate_create.json()["detail"]
    assert duplicate_grant.status_code == 400
    assert "already created a CMU" in duplicate_grant.json()["detail"]
    assert len(legacy_keysets) == 1
    assert len(keysets) == 2
    assert {item["id"] for item in keysets} == {
        legacy_keysets[0]["id"],
        cmu["keyset_id"],
    }
    assert keys.status_code == 200
    assert keys.json()["keysets"][0]["unit"] == cmu["unit"]
    assert keys.json()["keysets"][0]["friendly_alias"] == "Gym Guest Passes"
    assert keys.json()["keysets"][0]["friendly_unit_alias"] == "passes"
    assert keys.json()["keysets"][0]["keys"]
    assert grants == [
        {
            **grant,
            "uses": 1,
            "status": "consumed",
            "updated_at": grants[0]["updated_at"],
            "consumed_at": grants[0]["consumed_at"],
            "keyset_id": cmu["keyset_id"],
        }
    ]


def test_operator_can_update_cmu_display_labels(tmp_path) -> None:
    configured = settings(tmp_path)
    npub = "npub1treasurer0000000000000000000000000000000000000000"
    with TestClient(create_app(configured)) as client:
        client.post(
            "/v1/operator/treasurers",
            json={"npub": npub},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        grant = client.post(
            "/v1/operator/treasurer-grants",
            json={"npub": npub},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        ).json()
        created = client.post(
            "/v1/operator/cmus",
            json={"grant_id": grant["id"], "name": "Old Name"},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        ).json()
        updated = client.post(
            f"/v1/operator/cmus/{created['unit']}/label",
            json={"name": "Food Share Credits", "unit_alias": "shares"},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        keyset = client.get(f"/v1/keys/{created['keyset_id']}").json()["keysets"][0]
        partial = client.post(
            f"/v1/operator/cmus/{created['keyset_id']}/label",
            json={"unit_alias": "meals"},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        empty = client.post(
            f"/v1/operator/cmus/{created['unit']}/label",
            json={},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )

    assert updated.status_code == 200
    assert updated.json()["friendly_name"] == "Food Share Credits"
    assert updated.json()["friendly_alias"] == "Food Share Credits"
    assert updated.json()["friendly_unit_alias"] == "shares"
    assert keyset["friendly_alias"] == "Food Share Credits"
    assert keyset["friendly_unit_alias"] == "shares"
    assert partial.status_code == 200
    assert partial.json()["friendly_name"] == "Food Share Credits"
    assert partial.json()["friendly_unit_alias"] == "meals"
    assert empty.status_code == 400
    assert "at least one" in empty.json()["detail"]


def test_created_cmu_keyset_survives_restart(tmp_path) -> None:
    configured = settings(tmp_path)
    npub = "npub1treasurer0000000000000000000000000000000000000000"
    with TestClient(create_app(configured)) as client:
        client.post(
            "/v1/operator/treasurers",
            json={"npub": npub},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        grant = client.post(
            "/v1/operator/treasurer-grants",
            json={"npub": npub},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        ).json()
        created = client.post(
            "/v1/operator/cmus",
            json={"grant_id": grant["id"], "name": "Restart Credits"},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        ).json()

    with TestClient(create_app(configured)) as restarted:
        keysets = restarted.get("/v1/keysets").json()["keysets"]
        cmus = restarted.get(
            "/v1/operator/cmus",
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        ).json()["cmus"]

    assert created["keyset_id"] in {keyset["id"] for keyset in keysets}
    assert created in cmus


def test_created_cmu_can_issue_and_retire_independently(tmp_path) -> None:
    configured = settings(tmp_path)
    app = create_app(configured)
    legacy_keyset = app.state.keyset
    npub = "npub1treasurer0000000000000000000000000000000000000000"
    with TestClient(app) as client:
        client.post(
            "/v1/operator/treasurers",
            json={"npub": npub},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        grant = client.post(
            "/v1/operator/treasurer-grants",
            json={"npub": npub},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        ).json()
        created = client.post(
            "/v1/operator/cmus",
            json={"grant_id": grant["id"], "name": "Independent Credits"},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        ).json()
        created_keyset = app.state.store.keysets[created["keyset_id"]]

        legacy_proof = issue_proof(client, legacy_keyset, amount=8)
        created_proof = issue_proof(
            client,
            created_keyset,
            amount=8,
            secret="created-cmu-secret",
        )
        retired = client.post(
            "/v1/operator/retire",
            json={"inputs": [created_proof], "memo": "program completed"},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        cross_cmu_swap = client.post(
            "/v1/swap",
            json={
                "inputs": [legacy_proof],
                "outputs": [
                    blinded_output(created_keyset, 8, "cross-cmu-output", 43)[0]
                ],
            },
        )

    assert created_keyset.id != legacy_keyset.id
    assert created_keyset.unit == created["unit"]
    assert retired.status_code == 200
    assert retired.json()["unit"] == created["unit"]
    assert retired.json()["amount"] == 8
    assert cross_cmu_swap.status_code == 400
    assert "active keyset" in cross_cmu_swap.json()["detail"]


def test_treasurer_can_consume_grant_over_public_treasury_route(tmp_path) -> None:
    configured = settings(tmp_path)
    treasurer = Keys(priv_k="1".zfill(64))
    npub = treasurer.public_key_bech32()
    with TestClient(create_app(configured)) as client:
        client.post(
            "/v1/operator/treasurers",
            json={"npub": npub},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        grant = client.post(
            "/v1/operator/treasurer-grants",
            json={"npub": npub},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        ).json()
        envelope = build_cmu_create_envelope(
            mint="https://clear.example",
            grant_id=grant["id"],
            name="Treasurer Credits",
            unit_alias="credits",
            nsec=treasurer.private_key_bech32(),
        )
        created = client.post("/v1/treasury/cmus", json=envelope)
        replay = client.post("/v1/treasury/cmus", json=envelope)

    assert created.status_code == 200
    assert created.json()["friendly_name"] == "Treasurer Credits"
    assert created.json()["friendly_unit_alias"] == "credits"
    assert created.json()["treasurer_npub"] == npub
    assert replay.status_code == 400
    assert "not pending" in replay.json()["detail"]


def test_treasurer_can_inspect_bound_cmu_over_public_treasury_route(tmp_path) -> None:
    configured = settings(tmp_path)
    treasurer = Keys(priv_k="1".zfill(64))
    npub = treasurer.public_key_bech32()
    with TestClient(create_app(configured)) as client:
        client.post(
            "/v1/operator/treasurers",
            json={"npub": npub},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        grant = client.post(
            "/v1/operator/treasurer-grants",
            json={"npub": npub},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        ).json()
        created = client.post(
            "/v1/treasury/cmus",
            json=build_cmu_create_envelope(
                mint="https://clear.example",
                grant_id=grant["id"],
                name="Treasurer Credits",
                unit_alias="credits",
                nsec=treasurer.private_key_bech32(),
            ),
        ).json()
        envelope = build_cmu_info_envelope(
            mint="https://clear.example",
            nsec=treasurer.private_key_bech32(),
        )
        response = client.post("/v1/treasury/cmus/info", json=envelope)
        replay = client.post("/v1/treasury/cmus/info", json=envelope)

    assert response.status_code == 200
    assert response.json()["unit"] == created["unit"]
    assert response.json()["keyset_id"] == created["keyset_id"]
    assert response.json()["friendly_name"] == "Treasurer Credits"
    assert response.json()["friendly_unit_alias"] == "credits"
    assert response.json()["treasurer_npub"] == npub
    assert response.json()["treasurer_pubkey"] == treasurer.public_key_hex()
    assert replay.status_code == 400
    assert "nonce has already been used" in replay.json()["detail"]


def test_treasury_cmu_info_rejects_unbound_treasurer(tmp_path) -> None:
    configured = settings(tmp_path)
    treasurer = Keys(priv_k="1".zfill(64))
    with TestClient(create_app(configured)) as client:
        response = client.post(
            "/v1/treasury/cmus/info",
            json=build_cmu_info_envelope(
                mint="https://clear.example",
                nsec=treasurer.private_key_bech32(),
            ),
        )

    assert response.status_code == 400
    assert "does not control an active CMU" in response.json()["detail"]


def test_treasurer_can_authorize_quote_for_bound_cmu(tmp_path) -> None:
    configured = settings(tmp_path)
    treasurer = Keys(priv_k="1".zfill(64))
    npub = treasurer.public_key_bech32()
    with TestClient(create_app(configured)) as client:
        client.post(
            "/v1/operator/treasurers",
            json={"npub": npub},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        grant = client.post(
            "/v1/operator/treasurer-grants",
            json={"npub": npub},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        ).json()
        cmu = client.post(
            "/v1/treasury/cmus",
            json=build_cmu_create_envelope(
                mint="https://clear.example",
                grant_id=grant["id"],
                name="Treasurer Credits",
                nsec=treasurer.private_key_bech32(),
            ),
        ).json()
        quote = client.post(
            "/v1/mint/quote/clear",
            json={"amount": 8, "unit": cmu["unit"]},
        ).json()
        response = client.post(
            f"/v1/treasury/quotes/{quote['quote']}/authorize",
            json=build_quote_authorize_envelope(
                mint="https://clear.example",
                quote_id=quote["quote"],
                nsec=treasurer.private_key_bech32(),
            ),
        )

    assert response.status_code == 200
    assert response.json()["amount_paid"] == 8


def test_treasury_quote_authorization_rejects_wrong_treasurer(tmp_path) -> None:
    configured = settings(tmp_path)
    treasurer = Keys(priv_k="1".zfill(64))
    wrong = Keys(priv_k="2".zfill(64))
    with TestClient(create_app(configured)) as client:
        client.post(
            "/v1/operator/treasurers",
            json={"npub": treasurer.public_key_bech32()},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        grant = client.post(
            "/v1/operator/treasurer-grants",
            json={"npub": treasurer.public_key_bech32()},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        ).json()
        cmu = client.post(
            "/v1/treasury/cmus",
            json=build_cmu_create_envelope(
                mint="https://clear.example",
                grant_id=grant["id"],
                name="Treasurer Credits",
                nsec=treasurer.private_key_bech32(),
            ),
        ).json()
        quote = client.post(
            "/v1/mint/quote/clear",
            json={"amount": 8, "unit": cmu["unit"]},
        ).json()
        response = client.post(
            f"/v1/treasury/quotes/{quote['quote']}/authorize",
            json=build_quote_authorize_envelope(
                mint="https://clear.example",
                quote_id=quote["quote"],
                nsec=wrong.private_key_bech32(),
            ),
        )

    assert response.status_code == 400
    assert "does not match quote CMU" in response.json()["detail"]


def test_treasury_route_rejects_signature_from_wrong_treasurer(tmp_path) -> None:
    configured = settings(tmp_path)
    authorized = Keys(priv_k="1".zfill(64))
    wrong = Keys(priv_k="2".zfill(64))
    with TestClient(create_app(configured)) as client:
        client.post(
            "/v1/operator/treasurers",
            json={"npub": authorized.public_key_bech32()},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        grant = client.post(
            "/v1/operator/treasurer-grants",
            json={"npub": authorized.public_key_bech32()},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        ).json()
        envelope = build_cmu_create_envelope(
            mint="https://clear.example",
            grant_id=grant["id"],
            name="Wrong Signer",
            nsec=wrong.private_key_bech32(),
        )
        response = client.post("/v1/treasury/cmus", json=envelope)
        grants = client.get(
            "/v1/operator/treasurer-grants",
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        ).json()["grants"]

    assert response.status_code == 400
    assert "does not match grant treasurer" in response.json()["detail"]
    assert grants[0]["status"] == "pending"
    assert grants[0]["uses"] == 0


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
