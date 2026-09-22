from __future__ import annotations

import sqlite3
import time
from dataclasses import replace

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
    build_cmu_description_envelope,
    build_cmu_info_envelope,
    build_cmu_summary_envelope,
    build_cmu_visibility_envelope,
    build_quote_authorize_envelope,
    sign_payload,
)

MASTER_SECRET = "11" * 32
OPERATOR_TOKEN = "operator-token-that-is-long-enough"
MINT_SERVICE_NSEC = "22" * 32
MINT_SERVICE_NPUB = Keys(priv_k=MINT_SERVICE_NSEC).public_key_bech32()
MINT_SERVICE_FIPS_IPV6_ADDRESS = "fd12:6ef4:53c:5900:f315:6311:7f99:b6ea"


def settings(
    tmp_path,
    *,
    master_secret: str = MASTER_SECRET,
    currency_name: str = "Example Credits",
    mint_title: str = "Clear Mint",
    mint_tag_line: str = "Privately issued community value.",
    root_authority_npub: str | None = None,
    currency_alias: str | None = None,
    currency_unit_alias: str | None = None,
    root_api_loopback_only: bool = False,
    root_api_allowed_networks: str = (
        "127.0.0.0/8,::1/128,10.0.0.0/8,172.16.0.0/12,"
        "192.168.0.0/16,fc00::/7"
    ),
    mint_service_nsec: str | None = MINT_SERVICE_NSEC,
    mint_service_management: str = "independent",
) -> Settings:
    return Settings(
        database_path=tmp_path / "clear.sqlite3",
        master_secret=master_secret,
        operator_token=OPERATOR_TOKEN,
        currency_name=currency_name,
        mint_title=mint_title,
        mint_tag_line=mint_tag_line,
        mint_url="https://clear.example",
        max_order=10,
        root_authority_npub=root_authority_npub,
        currency_alias=currency_alias,
        currency_unit_alias=currency_unit_alias,
        root_api_loopback_only=root_api_loopback_only,
        root_api_allowed_networks=root_api_allowed_networks,
        mint_service_nsec=mint_service_nsec,
        mint_service_management=mint_service_management,
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


def commission_and_enable(client: TestClient) -> dict:
    headers = {"Authorization": f"Bearer {OPERATOR_TOKEN}"}
    verified = client.post(
        "/v1/operator/commissioning/verify",
        headers=headers,
    )
    assert verified.status_code == 200, verified.json()
    enabled = client.post("/v1/operator/treasury/enable", headers=headers)
    assert enabled.status_code == 200, enabled.json()
    return enabled.json()


def test_information_health_and_unique_currency(tmp_path) -> None:
    configured = settings(tmp_path)
    with TestClient(create_app(configured)) as client:
        info = client.get("/")
        health = client.get("/health")
        keys = client.get("/v1/keys")
        mint_info = client.get("/v1/info")

    assert health.json() == {
        "status": "ok",
        "service": "clear",
        "version": "0.1.0",
    }
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
    assert info.json()["service_identity"] == {
        "npub": MINT_SERVICE_NPUB,
        "fips_ipv6_address": MINT_SERVICE_FIPS_IPV6_ADDRESS,
        "type": "clear-mint",
        "management": "independent",
        "state": "bootstrapped",
        "descriptor_event_id": None,
        "operator": None,
    }
    assert mint_info.json()["service_identity"] == info.json()["service_identity"]
    assert MINT_SERVICE_NSEC not in info.text
    assert MINT_SERVICE_NSEC not in mint_info.text


def test_treasury_starts_disabled_and_enable_requires_verification(tmp_path) -> None:
    headers = {"Authorization": f"Bearer {OPERATOR_TOKEN}"}
    with TestClient(create_app(settings(tmp_path))) as client:
        status = client.get("/v1/operator/treasury", headers=headers)
        enable = client.post("/v1/operator/treasury/enable", headers=headers)

    assert status.status_code == 200
    assert status.json()["lifecycle"] == "bootstrapped"
    assert status.json()["verification_current"] is False
    assert status.json()["treasury_enabled"] is False
    assert status.json()["verification"] is None
    assert enable.status_code == 400
    assert "successful root verification" in enable.json()["detail"]


def test_store_transaction_rolls_back_when_operation_fails(tmp_path) -> None:
    app = create_app(settings(tmp_path))
    with TestClient(app):
        with pytest.raises(RuntimeError, match="simulated failure"):
            with app.state.store._transaction() as connection:
                connection.execute(
                    "INSERT INTO mint_metadata(key, value) VALUES ('test', 'partial')"
                )
                raise RuntimeError("simulated failure")
        with app.state.store._connection() as connection:
            row = connection.execute(
                "SELECT value FROM mint_metadata WHERE key = 'test'"
            ).fetchone()

    assert row is None


def test_root_verification_uses_isolated_keyset_and_records_evidence(tmp_path) -> None:
    headers = {"Authorization": f"Bearer {OPERATOR_TOKEN}"}
    app = create_app(settings(tmp_path))
    root_keyset_id = app.state.keyset.id
    with TestClient(app) as client:
        verified = client.post(
            "/v1/operator/commissioning/verify",
            headers=headers,
        )
        root_summary = client.get("/v1/operator/summary", headers=headers)
        keysets = client.get("/v1/keysets").json()["keysets"]
        verification = verified.json()["verification"]
        commissioning = next(
            keyset
            for keyset in keysets
            if keyset["id"] == verification["keyset_id"]
        )
        rejected_quote = client.post(
            "/v1/mint/quote/clear",
            json={"amount": 1, "unit": commissioning["unit"]},
        )

    assert verified.status_code == 200, verified.json()
    assert verified.json()["lifecycle"] == "root-verified"
    assert verified.json()["verification_current"] is True
    assert verified.json()["treasury_enabled"] is False
    assert verification["status"] == "successful"
    assert verification["issued"] == 3
    assert verification["retired"] == 3
    assert verification["evidence"]["digest"]
    assert all(
        check["passed"] for check in verification["evidence"]["checks"]
    )
    assert root_summary.json()["keyset_id"] == root_keyset_id
    assert root_summary.json()["issued"] == 0
    assert root_summary.json()["outstanding"] == 0
    assert commissioning["active"] is False
    assert rejected_quote.status_code == 400
    assert "not active" in rejected_quote.json()["detail"]


def test_operator_metrics_distinguish_supply_from_proof_state(tmp_path) -> None:
    configured = settings(tmp_path)
    headers = {"Authorization": f"Bearer {OPERATOR_TOKEN}"}
    app = create_app(configured)
    keyset = app.state.keyset
    with TestClient(app) as client:
        proof = issue_proof(client, keyset, amount=8, secret="metric-source")
        first_output, first_r = blinded_output(keyset, 4, "metric-swap-a", 31)
        second_output, _second_r = blinded_output(keyset, 4, "metric-swap-b", 37)
        swapped = client.post(
            "/v1/swap",
            json={
                "inputs": [proof],
                "outputs": [first_output, second_output],
            },
        )
        assert swapped.status_code == 200, swapped.json()
        first_swapped = unblind(
            keyset,
            4,
            "metric-swap-a",
            first_r,
            swapped.json()["signatures"][0],
        )
        retired = client.post(
            "/v1/operator/retire",
            json={"inputs": [first_swapped], "memo": "redeemed for test"},
            headers=headers,
        )
        assert retired.status_code == 200, retired.json()
        unauthorized = client.get("/v1/operator/metrics")
        metrics = client.get("/v1/operator/metrics", headers=headers)
        filtered = client.get(
            "/v1/operator/metrics",
            params={"keyset_id": keyset.id},
            headers=headers,
        )

    assert unauthorized.status_code == 401
    assert metrics.status_code == 200, metrics.json()
    assert filtered.status_code == 200, filtered.json()
    assert metrics.json() == filtered.json()
    aggregate = metrics.json()["aggregate"]
    assert aggregate["issued"] == 8
    assert aggregate["retired"] == 4
    assert aggregate["outstanding"] == 4
    assert aggregate["signed_outputs_amount"] == 16
    assert aggregate["spent_proofs_amount"] == 12
    assert aggregate["unspent_signed_outputs_estimate"] == 4
    cmu = metrics.json()["cmus"][0]
    assert cmu["unit"] == keyset.unit
    assert cmu["supply"] == {"issued": 8, "retired": 4, "outstanding": 4}
    assert cmu["quotes"] == {
        "count": 1,
        "requested": 8,
        "authorized": 8,
        "issued": 8,
        "authorized_unissued": 0,
        "requested_unauthorized": 0,
    }
    assert cmu["activity"]["audit_actions"]["issue"] == {"amount": 8, "count": 1}
    assert cmu["activity"]["audit_actions"]["swap"] == {"amount": 8, "count": 1}
    assert cmu["activity"]["audit_actions"]["retire"] == {"amount": 4, "count": 1}
    assert cmu["proof_state"]["signed_outputs_by_operation"]["issue"] == {
        "amount": 8,
        "count": 1,
    }
    assert cmu["proof_state"]["signed_outputs_by_operation"]["swap"] == {
        "amount": 8,
        "count": 2,
    }
    assert cmu["proof_state"]["spent_proofs_by_reason"]["swap"] == {
        "amount": 8,
        "count": 1,
    }
    assert cmu["proof_state"]["spent_proofs_by_reason"]["retire"] == {
        "amount": 4,
        "count": 1,
    }


def test_treasury_enablement_survives_restart_and_can_be_disabled(tmp_path) -> None:
    configured = settings(tmp_path)
    headers = {"Authorization": f"Bearer {OPERATOR_TOKEN}"}
    with TestClient(create_app(configured)) as client:
        enabled = commission_and_enable(client)

    with TestClient(create_app(configured)) as restarted:
        retained = restarted.get("/v1/operator/treasury", headers=headers)
        disabled = restarted.post(
            "/v1/operator/treasury/disable",
            json={"reason": "operator maintenance"},
            headers=headers,
        )

    assert enabled["lifecycle"] == "treasury-enabled"
    assert retained.json()["treasury_enabled"] is True
    assert disabled.json()["lifecycle"] == "root-verified"
    assert disabled.json()["treasury_enabled"] is False
    assert disabled.json()["treasury_reason"] == "operator maintenance"


def test_disable_blocks_signed_mutations_but_not_existing_note_swaps(tmp_path) -> None:
    configured = settings(tmp_path)
    headers = {"Authorization": f"Bearer {OPERATOR_TOKEN}"}
    treasurer = Keys(priv_k="1".zfill(64))
    app = create_app(configured)
    with TestClient(app) as client:
        commission_and_enable(client)
        client.post(
            "/v1/operator/treasurers",
            json={"npub": treasurer.public_key_bech32()},
            headers=headers,
        )
        grant = client.post(
            "/v1/operator/treasurer-grants",
            json={"npub": treasurer.public_key_bech32()},
            headers=headers,
        ).json()
        proof = issue_proof(client, app.state.keyset, amount=1)
        client.post(
            "/v1/operator/treasury/disable",
            json={"reason": "operator maintenance"},
            headers=headers,
        )
        blocked = client.post(
            "/v1/treasury/cmus",
            json=build_cmu_create_envelope(
                mint=configured.mint_url,
                grant_id=grant["id"],
                name="Blocked Credits",
                nsec=treasurer.private_key_bech32(),
            ),
        )
        output, _ = blinded_output(
            app.state.keyset,
            1,
            "replacement-after-disable",
            29,
        )
        swapped = client.post(
            "/v1/swap",
            json={"inputs": [proof], "outputs": [output]},
        )

    assert blocked.status_code == 400
    assert "treasury operations are disabled" in blocked.json()["detail"]
    assert swapped.status_code == 200
    assert len(swapped.json()["signatures"]) == 1


def test_critical_configuration_change_invalidates_enablement(tmp_path) -> None:
    configured = settings(tmp_path)
    headers = {"Authorization": f"Bearer {OPERATOR_TOKEN}"}
    with TestClient(create_app(configured)) as client:
        commission_and_enable(client)

    changed = replace(configured, mint_url="https://moved-clear.example")
    with TestClient(create_app(changed)) as restarted:
        status = restarted.get("/v1/operator/treasury", headers=headers)

    assert status.json()["lifecycle"] == "verification-required"
    assert status.json()["verification_current"] is False
    assert status.json()["treasury_enabled"] is False
    assert "configuration change" in status.json()["treasury_reason"]


def test_failed_verification_is_durable_and_keeps_gate_closed(
    tmp_path, monkeypatch
) -> None:
    headers = {"Authorization": f"Bearer {OPERATOR_TOKEN}"}
    app = create_app(settings(tmp_path))

    def fail_swap(*args, **kwargs):
        raise ClearError("simulated swap failure")

    monkeypatch.setattr(app.state.store, "swap", fail_swap)
    with TestClient(app) as client:
        response = client.post(
            "/v1/operator/commissioning/verify",
            headers=headers,
        )
        status = client.get("/v1/operator/treasury", headers=headers)

    assert response.status_code == 400
    assert "simulated swap failure" in response.json()["detail"]
    assert status.json()["lifecycle"] == "verification-failed"
    assert status.json()["treasury_enabled"] is False
    assert status.json()["verification"]["failure_reason"] == (
        "simulated swap failure"
    )


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
    assert homepage.headers["content-language"] == "en"
    assert homepage.headers["vary"] == "Accept-Language"
    assert '<html lang="en" dir="ltr">' in homepage.text
    assert '<select id="language" name="lang"' in homepage.text
    assert '<option value="en" selected>English</option>' in homepage.text
    assert "<h1><bdi dir=\"auto\">Clear Mint</bdi></h1>" in homepage.text
    assert "Privately issued community value." in homepage.text
    assert "Harbour Lab Credits" in homepage.text
    assert "smiles" in homepage.text
    assert "Mint Units In Circulation" in homepage.text
    assert "Units Outstanding" in homepage.text
    assert "https://clear.example" in homepage.text
    assert "Copy mint URL" in homepage.text
    assert "Credit-Liability Ecash: Authorized and Redeemable" in homepage.text
    assert "Service identity" in homepage.text
    assert MINT_SERVICE_NPUB in homepage.text
    assert "FIPS IPv6 address" in homepage.text
    assert MINT_SERVICE_FIPS_IPV6_ADDRESS in homepage.text
    assert "Management" in homepage.text
    assert "independent" in homepage.text
    assert "Identity state" in homepage.text
    assert "bootstrapped" in homepage.text
    assert "Not commissioned" in homepage.text
    assert 'href="v1/info"' in homepage.text
    assert 'href="/v1/info"' not in homepage.text
    assert '<a href="https://trbouma.github.io/clear/">Docs</a>' in homepage.text
    assert 'href="docs"' not in homepage.text
    assert "API documentation" not in homepage.text
    assert "About Clear" not in homepage.text
    assert information.json()["currency"]["friendly_alias"] == (
        "Harbour Lab Credits"
    )


def test_browser_homepage_lists_active_keysets(tmp_path) -> None:
    configured = settings(
        tmp_path,
        currency_alias="Harbour Lab Credits",
        currency_unit_alias="smiles",
    )
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
            json={
                "grant_id": grant["id"],
                "name": "Gym Guest Passes",
                "unit_alias": "passes",
            },
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        ).json()
        created_keyset = client.app.state.store.keysets[created["keyset_id"]]
        issue_proof(
            client,
            created_keyset,
            amount=8,
            secret="homepage-created-cmu-proof",
        )
        homepage = client.get("/", headers={"Accept": "text/html"})
        metrics_page = client.get(f"/cmus/{created['keyset_id']}")

        unit_page = client.get(f"/cmus/{created['unit']}")
        assert unit_page.status_code == 200
        assert unit_page.text == metrics_page.text
        assert "Listed" in unit_page.text
        keysets = client.get("/v1/keysets").json()["keysets"]

    assert homepage.status_code == 200
    assert "Mint Units In Circulation" in homepage.text
    assert "Authorized treasury keyset" not in homepage.text
    assert npub in metrics_page.text
    assert f'data-profile-url="v1/nostr/profiles/{npub}"' not in homepage.text
    table = homepage.text.split('<table class="keyset-table">')[1].split('</table>')[0]
    assert table.count('<th>') == 4
    assert '<th>Units Outstanding</th>' in table
    assert '<th>Authority</th>' not in table
    assert '<th>Keyset ID</th>' not in table
    assert 'id="profile-card"' in homepage.text
    assert "Harbour Lab Credits" in homepage.text
    assert "Gym Guest Passes" in homepage.text
    assert "passes" in homepage.text
    assert "Outstanding" in homepage.text
    assert f'href="cmus/{created["keyset_id"]}"' in homepage.text
    assert created["unit"] in homepage.text
    assert created["keyset_id"] in homepage.text
    assert metrics_page.status_code == 200
    assert metrics_page.headers["content-language"] == "en"
    assert "CMU metrics" in metrics_page.text
    assert "Gym Guest Passes" in metrics_page.text
    assert "Policy-aware supply metrics" not in metrics_page.text
    assert (
        "<span>Issued</span><strong><bdi dir=\"auto\">8</bdi></strong>"
        in metrics_page.text
    )
    assert (
        "<span>Outstanding</span><strong><bdi dir=\"auto\">8</bdi></strong>"
        in metrics_page.text
    )
    assert "Quote pipeline" in metrics_page.text
    assert "Proof-state diagnostics" in metrics_page.text
    assert "Signed outputs by operation" in metrics_page.text
    assert "Spent proofs by reason" in metrics_page.text
    assert {item["authority"] for item in keysets} == {
        "operator",
        "authorized-treasury",
    }
    assert all(item["public_listing"] is True for item in keysets)
    assert next(
        item for item in keysets if item["authority"] == "authorized-treasury"
    )["treasurer_npub"] == npub
    assert next(item for item in keysets if item["authority"] == "operator")[
        "treasurer_npub"
    ] is None


def test_public_nostr_profile_endpoint_returns_kind_0_profile(
    tmp_path,
    monkeypatch,
) -> None:
    configured = settings(tmp_path)
    treasurer = Keys(priv_k="66" * 32)
    npub = treasurer.public_key_bech32()
    calls = []

    async def fake_lookup(value, *, relays=None, timeout=2.0):
        calls.append((value, relays, timeout))
        return {
            "npub": npub,
            "pubkey": treasurer.public_key_hex(),
            "profile": {
                "name": "Workshop Treasurer",
                "nip05": "treasurer@example.com",
            },
            "relays": relays,
        }

    monkeypatch.setattr("clear.main.lookup_nostr_profile", fake_lookup)
    with TestClient(create_app(configured)) as client:
        response = client.get(
            f"/v1/nostr/profiles/{npub}",
            params={"relay": "wss://relay.example", "timeout": "3"},
        )

    assert response.status_code == 200
    assert calls == [(npub, ["wss://relay.example"], 3.0)]
    assert response.json()["profile"]["name"] == "Workshop Treasurer"
    assert response.json()["profile"]["nip05"] == "treasurer@example.com"


def test_operator_can_make_cmu_private_without_disabling_direct_use(
    tmp_path,
) -> None:
    configured = settings(
        tmp_path,
        currency_alias="Harbour Lab Credits",
        currency_unit_alias="smiles",
    )
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
            json={
                "grant_id": grant["id"],
                "name": "Private Guest Passes",
                "unit_alias": "passes",
            },
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        ).json()
        private = client.post(
            f"/v1/operator/cmus/{created['unit']}/visibility",
            json={"public_listing": False},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        homepage = client.get("/", headers={"Accept": "text/html"})
        keysets = client.get("/v1/keysets").json()["keysets"]
        keys = client.get(f"/v1/keys/{created['keyset_id']}")
        metrics_page = client.get(f"/cmus/{created['keyset_id']}")
        unit_page = client.get(f"/cmus/{created['unit']}")
        assert unit_page.status_code == 200
        assert unit_page.text == metrics_page.text
        assert "Unlisted" in unit_page.text

    assert private.status_code == 200
    assert private.json()["public_listing"] is False
    assert "Private Guest Passes" not in homepage.text
    assert created["unit"] not in homepage.text
    assert created["keyset_id"] not in homepage.text
    assert "Harbour Lab Credits" in homepage.text
    private_keyset = next(
        item for item in keysets if item["id"] == created["keyset_id"]
    )
    assert private_keyset["public_listing"] is False
    assert private_keyset["active"] is True
    assert keys.status_code == 200
    assert keys.json()["keysets"][0]["unit"] == created["unit"]
    assert keys.json()["keysets"][0]["public_listing"] is False
    assert metrics_page.status_code == 200
    assert "Private Guest Passes" in metrics_page.text


def test_operator_can_publish_private_cmu_again(tmp_path) -> None:
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
            json={"grant_id": grant["id"], "name": "Workshop Passes"},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        ).json()
        client.post(
            f"/v1/operator/cmus/{created['keyset_id']}/visibility",
            json={"public_listing": False},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        published = client.post(
            f"/v1/operator/cmus/{created['unit']}/visibility",
            json={"public_listing": True},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        homepage = client.get("/", headers={"Accept": "text/html"})

    assert published.status_code == 200
    assert published.json()["public_listing"] is True
    assert "Workshop Passes" in homepage.text


def test_browser_homepage_uses_configured_mint_title(tmp_path) -> None:
    configured = settings(
        tmp_path,
        mint_title="Harbour Credit Service",
        mint_tag_line="Community credits for neighbourly exchange.",
        currency_alias="Harbour Lab Credits",
    )
    with TestClient(create_app(configured)) as client:
        homepage = client.get("/", headers={"Accept": "text/html"})

    assert homepage.status_code == 200
    assert "<h1><bdi dir=\"auto\">Harbour Credit Service</bdi></h1>" in homepage.text
    assert "Community credits for neighbourly exchange." in homepage.text
    assert "Harbour Lab Credits" in homepage.text


def test_browser_homepage_can_be_rendered_in_french(tmp_path) -> None:
    configured = settings(
        tmp_path,
        currency_alias="Harbour Lab Credits",
        currency_unit_alias="smiles",
    )
    with TestClient(create_app(configured)) as client:
        homepage = client.get(
            "/?lang=fr",
            headers={"Accept": "text/html", "Accept-Language": "en"},
        )
        information = client.get(
            "/?lang=fr",
            headers={"Accept": "application/json"},
        )

    assert homepage.status_code == 200
    assert homepage.headers["content-language"] == "fr"
    assert '<html lang="fr" dir="ltr">' in homepage.text
    assert '<option value="fr" selected>Français</option>' in homepage.text
    assert "Détails du service" in homepage.text
    assert "Fonctionnement du service" not in homepage.text
    assert "Identité du service" in homepage.text
    assert "Copier l’URL du service" in homepage.text
    assert "Harbour Lab Credits" in homepage.text
    assert "smiles" in homepage.text
    assert MINT_SERVICE_NPUB in homepage.text
    assert information.json()["description"] == (
        "Credit-Liability Ecash: Authorized and Redeemable"
    )


def test_browser_homepage_uses_accept_language_without_a_selector(tmp_path) -> None:
    with TestClient(create_app(settings(tmp_path))) as client:
        homepage = client.get(
            "/",
            headers={
                "Accept": "text/html",
                "Accept-Language": "fr-CA,fr;q=0.9,en;q=0.5",
            },
        )

    assert homepage.status_code == 200
    assert '<html lang="fr" dir="ltr">' in homepage.text
    assert "En ligne" in homepage.text


def test_browser_homepage_renders_arabic_with_isolated_technical_values(
    tmp_path,
) -> None:
    configured = settings(
        tmp_path,
        currency_alias="Harbour Lab Credits",
        currency_unit_alias="smiles",
    )
    with TestClient(create_app(configured)) as client:
        homepage = client.get(
            "/?lang=ar",
            headers={"Accept": "text/html"},
        )
        information = client.get(
            "/?lang=ar",
            headers={"Accept": "application/json"},
        )

    assert homepage.status_code == 200
    assert homepage.headers["content-language"] == "ar"
    assert '<html lang="ar" dir="rtl">' in homepage.text
    assert '<option value="ar" selected>العربية</option>' in homepage.text
    assert "تفاصيل الخدمة" in homepage.text
    assert "كيفية عمل هذه الخدمة" not in homepage.text
    assert '<bdi dir="auto">Harbour Lab Credits</bdi>' in homepage.text
    assert (
        '<code class="technical" id="mint-url" dir="ltr">'
        "https://clear.example</code>"
    ) in homepage.text
    assert MINT_SERVICE_NPUB in homepage.text
    assert information.json()["description"] == (
        "Credit-Liability Ecash: Authorized and Redeemable"
    )


def test_browser_homepage_negotiates_arabic_region_locale(tmp_path) -> None:
    with TestClient(create_app(settings(tmp_path))) as client:
        homepage = client.get(
            "/",
            headers={
                "Accept": "text/html",
                "Accept-Language": "ar-EG,ar;q=0.9,en;q=0.5",
            },
        )

    assert homepage.headers["content-language"] == "ar"
    assert '<html lang="ar" dir="rtl">' in homepage.text
    assert "متصل" in homepage.text


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


def test_operator_api_allows_internal_network_client(tmp_path) -> None:
    configured = settings(tmp_path, root_api_loopback_only=False)
    app = create_app(configured)
    headers = {"Authorization": f"Bearer {OPERATOR_TOKEN}"}

    with TestClient(app, client=("172.18.0.12", 50000)) as internal_client:
        accepted = internal_client.get("/v1/operator/summary", headers=headers)

    assert accepted.status_code == 200


def test_operator_api_blocks_external_network_client(tmp_path) -> None:
    configured = settings(tmp_path, root_api_loopback_only=False)
    app = create_app(configured)
    headers = {"Authorization": f"Bearer {OPERATOR_TOKEN}"}

    with TestClient(app, client=("203.0.113.10", 50000)) as remote_client:
        rejected = remote_client.get("/v1/operator/summary", headers=headers)

    assert rejected.status_code == 403
    assert rejected.json() == {
        "detail": "operator API requires internal network access"
    }


def test_operator_api_blocks_external_forwarded_client(tmp_path) -> None:
    configured = settings(tmp_path, root_api_loopback_only=False)
    app = create_app(configured)
    headers = {
        "Authorization": f"Bearer {OPERATOR_TOKEN}",
        "X-Forwarded-For": "203.0.113.10",
    }

    with TestClient(app, client=("172.18.0.12", 50000)) as proxy_client:
        rejected = proxy_client.get("/v1/operator/summary", headers=headers)

    assert rejected.status_code == 403
    assert rejected.json() == {
        "detail": "operator API requires internal network access"
    }


def test_public_surface_does_not_register_operator_routes(tmp_path) -> None:
    app = create_app(settings(tmp_path), surface="public")
    headers = {"Authorization": f"Bearer {OPERATOR_TOKEN}"}

    with TestClient(app, client=("127.0.0.1", 50000)) as client:
        info = client.get("/v1/info")
        operator = client.get("/v1/operator/summary", headers=headers)

    assert info.status_code == 200
    assert operator.status_code == 404


def test_operator_surface_only_registers_operator_routes(tmp_path) -> None:
    app = create_app(settings(tmp_path), surface="operator")
    headers = {"Authorization": f"Bearer {OPERATOR_TOKEN}"}

    with TestClient(app, client=("127.0.0.1", 50000)) as client:
        health = client.get("/health")
        info = client.get("/v1/info")
        operator = client.get("/v1/operator/summary", headers=headers)

    assert health.status_code == 200
    assert info.status_code == 404
    assert operator.status_code == 200


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


def test_operator_root_send_uses_root_wallet_and_delivery_helpers(
    tmp_path,
    monkeypatch,
) -> None:
    configured = settings(tmp_path)
    app = create_app(configured)
    keyset = app.state.keyset
    calls = {}

    def fake_discover(address, *, mint_url, unit):
        calls["discover"] = {"address": address, "mint_url": mint_url, "unit": unit}
        return {
            "supported": True,
            "mint": mint_url,
            "unit": unit,
            "recipient_pubkey": "ab" * 32,
            "recipient_npub": "npub1recipient",
            "relays": ["ws://spurline:8080"],
        }

    def fake_export_or_swap(amount, wallet_path, *, api_url, memo):
        calls["export_or_swap"] = {
            "amount": amount,
            "api_url": api_url,
            "memo": memo,
        }
        return {"token": "cashu-token"}

    def fake_deliver(discovery, *, token, amount, memo, relays, expiration):
        calls["deliver"] = {
            "token": token,
            "amount": amount,
            "memo": memo,
            "relays": relays,
            "expiration": expiration,
        }
        return {
            "delivery": {"recipient_npub": "npub1recipient"},
            "publish": {"status": "OK", "verified": True},
        }

    def fake_export_token(amount, wallet_path, *, memo, remove):
        calls["export_token"] = {"amount": amount, "memo": memo, "remove": remove}
        return {
            "mint": configured.mint_url,
            "unit": keyset.unit,
            "amount": amount,
            "token": "cashu-token",
            "proofs": [{"secret": "proof-secret"}],
        }

    monkeypatch.setattr("clear.main.discover_clear_support", fake_discover)
    monkeypatch.setattr("clear.main._export_or_swap", fake_export_or_swap)
    monkeypatch.setattr("clear.main.deliver_clear_token", fake_deliver)
    monkeypatch.setattr("clear.main.export_token", fake_export_token)
    monkeypatch.setenv("CLEAR_ROOT_API_URL", "http://127.0.0.1:3340")

    with TestClient(app) as client:
        response = client.post(
            "/v1/operator/root/send",
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
            json={
                "amount": 25,
                "address": "ab" * 32,
                "memo": "initial distribution",
                "relays": ["ws://spurline:8080"],
                "allow_internal_mint_delivery": True,
            },
        )

    assert response.status_code == 200
    assert response.json()["amount"] == 25
    assert calls["discover"] == {
        "address": "ab" * 32,
        "mint_url": configured.mint_url,
        "unit": keyset.unit,
    }
    assert calls["export_or_swap"]["api_url"] == "http://127.0.0.1:3340"
    assert calls["deliver"]["relays"] == ["ws://spurline:8080"]
    assert calls["export_token"]["remove"] is True


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
    assert granted.json()["mint_url"] == configured.mint_url.rstrip("/")
    assert granted.json()["scope"] == "keyset:create"
    assert granted.json()["max_uses"] == 1
    assert granted.json()["uses"] == 0
    assert granted.json()["status"] == "pending"
    assert granted.json()["keyset_id"] is None
    assert duplicate_pending.status_code == 400
    assert "unused grant" in duplicate_pending.json()["detail"]
    assert listed.json()["grants"] == [granted.json()]


def test_operator_revokes_pending_grant_and_can_replace_it(tmp_path) -> None:
    configured = settings(tmp_path)
    app = create_app(configured)
    treasurer = Keys(priv_k="1".zfill(64))
    npub = treasurer.public_key_bech32()
    headers = {"Authorization": f"Bearer {OPERATOR_TOKEN}"}
    with TestClient(app) as client:
        commission_and_enable(client)
        store = app.state.store
        store.add_treasurer(npub)
        grant = store.grant_treasurer(npub)
        route = f'/v1/operator/treasurer-grants/{grant["id"]}/revoke'
        assert client.post(route).status_code != 200
        assert store.get_treasurer_grant(grant["id"])["status"] == "pending"
        revoked = client.post(route, headers=headers)
        assert revoked.status_code == 200
        assert revoked.json()["status"] == "revoked"
        assert revoked.json()["mint_url"] == configured.mint_url.rstrip("/")
        assert revoked.json()["updated_at"] > grant["updated_at"]
        assert revoked.json()["uses"] == 0
        assert revoked.json()["keyset_id"] is None
        assert revoked.json()["consumed_at"] is None
        assert client.post(route, headers=headers).status_code == 400
        assert client.post('/v1/operator/treasurer-grants/missing/revoke', headers=headers).status_code == 400
        operator_create = client.post('/v1/operator/cmus', json={"grant_id": grant["id"]}, headers=headers)
        assert operator_create.status_code == 400
        treasury_create = client.post('/v1/treasury/cmus', json=build_cmu_create_envelope(
            mint=configured.mint_url, grant_id=grant["id"],
            nsec=treasurer.private_key_bech32(), name="Revoked",
        ))
        assert treasury_create.status_code == 400
        replacement = client.post('/v1/operator/treasurer-grants', json={"npub": npub}, headers=headers).json()
        assert replacement["id"] != grant["id"]
        assert replacement["status"] == "pending"
        created = client.post('/v1/operator/cmus', json={"grant_id": replacement["id"]}, headers=headers)
        assert created.status_code == 200
        assert client.post(f'/v1/operator/treasurer-grants/{replacement["id"]}/revoke', headers=headers).status_code == 400
        assert store.get_cmu(created.json()["unit"])["status"] == "active"
    with TestClient(create_app(configured)) as client:
        grants = client.get('/v1/operator/treasurer-grants', headers=headers).json()["grants"]
        assert next(g for g in grants if g["id"] == grant["id"])["status"] == "revoked"
    with sqlite3.connect(configured.database_path) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM audit_log WHERE action = 'treasurer:grant-revoke' AND reference = ?",
            (grant["id"],),
        ).fetchone()[0]
    assert count == 1


def test_store_allows_new_grant_after_treasurer_created_cmu(tmp_path) -> None:
    configured = settings(tmp_path)
    app = create_app(configured)
    npub = "npub1treasurer0000000000000000000000000000000000000000"
    with TestClient(app):
        app.state.store.add_treasurer(npub)
        grant = app.state.store.grant_treasurer(npub)
        consumed = app.state.store.consume_treasurer_grant(
            grant["id"], "keyset-created-by-grant"
        )
        next_grant = app.state.store.grant_treasurer(npub)

    assert consumed["status"] == "consumed"
    assert consumed["uses"] == 1
    assert consumed["keyset_id"] == "keyset-created-by-grant"
    assert next_grant["status"] == "pending"
    assert next_grant["npub"] == npub
    assert next_grant["keyset_id"] is None


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
        next_grant = client.post(
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
    assert next_grant.status_code == 200
    assert next_grant.json()["npub"] == npub
    assert next_grant.json()["status"] == "pending"
    assert next_grant.json()["keyset_id"] is None
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
    grants_by_id = {item["id"]: item for item in grants}
    assert grants_by_id[grant["id"]] == {
        **grant,
        "uses": 1,
        "status": "consumed",
        "updated_at": grants_by_id[grant["id"]]["updated_at"],
        "consumed_at": grants_by_id[grant["id"]]["consumed_at"],
        "keyset_id": cmu["keyset_id"],
    }
    assert grants_by_id[next_grant.json()["id"]] == next_grant.json()


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
        commission_and_enable(client)
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
        commission_and_enable(client)
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
            keyset_id=created["keyset_id"],
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


def test_treasurer_selects_cmu_when_multiple_are_active(tmp_path) -> None:
    configured = settings(tmp_path)
    treasurer = Keys(priv_k="1".zfill(64))
    npub = treasurer.public_key_bech32()
    with TestClient(create_app(configured)) as client:
        commission_and_enable(client)
        client.post(
            "/v1/operator/treasurers",
            json={"npub": npub},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        first_grant = client.post(
            "/v1/operator/treasurer-grants",
            json={"npub": npub},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        ).json()
        first_cmu = client.post(
            "/v1/treasury/cmus",
            json=build_cmu_create_envelope(
                mint="https://clear.example",
                grant_id=first_grant["id"],
                name="First Credits",
                nsec=treasurer.private_key_bech32(),
            ),
        ).json()
        second_grant = client.post(
            "/v1/operator/treasurer-grants",
            json={"npub": npub},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        ).json()
        second_cmu = client.post(
            "/v1/treasury/cmus",
            json=build_cmu_create_envelope(
                mint="https://clear.example",
                grant_id=second_grant["id"],
                name="Second Credits",
                nsec=treasurer.private_key_bech32(),
            ),
        ).json()
        now = int(time.time())
        missing_keyset_payload = {
            "action": "cmu:info",
            "mint": "https://clear.example",
            "nonce": "ab" * 32,
            "created_at": now,
            "expires_at": now + 300,
        }
        missing_keyset = client.post(
            "/v1/treasury/cmus/info",
            json={
                "payload": missing_keyset_payload,
                "event": sign_payload(
                    missing_keyset_payload,
                    treasurer.private_key_bech32(),
                ),
            },
        )
        selected = client.post(
            "/v1/treasury/cmus/info",
            json=build_cmu_info_envelope(
                mint="https://clear.example",
                nsec=treasurer.private_key_bech32(),
                keyset_id=second_cmu["keyset_id"],
            ),
        )

    assert first_cmu["keyset_id"] != second_cmu["keyset_id"]
    assert missing_keyset.status_code == 400
    assert "keyset_id is required" in missing_keyset.json()["detail"]
    assert selected.status_code == 200
    assert selected.json()["keyset_id"] == second_cmu["keyset_id"]
    assert selected.json()["friendly_name"] == "Second Credits"


def test_treasurer_can_inspect_bound_cmu_supply_summary(tmp_path) -> None:
    configured = settings(tmp_path)
    treasurer = Keys(priv_k="1".zfill(64))
    npub = treasurer.public_key_bech32()
    app = create_app(configured)
    with TestClient(app) as client:
        commission_and_enable(client)
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
        created_keyset = app.state.store.keysets[cmu["keyset_id"]]
        proof = issue_proof(
            client,
            created_keyset,
            amount=8,
            secret="treasurer-summary-secret",
        )
        retired = client.post(
            "/v1/operator/retire",
            json={"inputs": [proof], "memo": "program completed"},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        envelope = build_cmu_summary_envelope(
            mint="https://clear.example",
            nsec=treasurer.private_key_bech32(),
            keyset_id=cmu["keyset_id"],
        )
        response = client.post("/v1/treasury/cmus/summary", json=envelope)
        replay = client.post("/v1/treasury/cmus/summary", json=envelope)

    assert retired.status_code == 200
    assert response.status_code == 200
    assert response.json() == {
        "unit": cmu["unit"],
        "keyset_id": cmu["keyset_id"],
        "issued": 8,
        "retired": 8,
        "circulating": 0,
        "outstanding": 0,
        "treasurer_pubkey": treasurer.public_key_hex(),
    }
    assert replay.status_code == 400
    assert "nonce has already been used" in replay.json()["detail"]


def test_treasurer_can_make_bound_cmu_private_and_publish_again(tmp_path) -> None:
    configured = settings(tmp_path)
    treasurer = Keys(priv_k="1".zfill(64))
    npub = treasurer.public_key_bech32()
    with TestClient(create_app(configured)) as client:
        commission_and_enable(client)
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
                name="Treasurer Private Credits",
                nsec=treasurer.private_key_bech32(),
            ),
        ).json()
        private_envelope = build_cmu_visibility_envelope(
            mint="https://clear.example",
            nsec=treasurer.private_key_bech32(),
            keyset_id=cmu["keyset_id"],
            public_listing=False,
        )
        private = client.post("/v1/treasury/cmus/visibility", json=private_envelope)
        replay = client.post("/v1/treasury/cmus/visibility", json=private_envelope)
        private_homepage = client.get("/", headers={"Accept": "text/html"})
        keysets = client.get("/v1/keysets").json()["keysets"]
        published = client.post(
            "/v1/treasury/cmus/visibility",
            json=build_cmu_visibility_envelope(
                mint="https://clear.example",
                nsec=treasurer.private_key_bech32(),
                keyset_id=cmu["keyset_id"],
                public_listing=True,
            ),
        )
        public_homepage = client.get("/", headers={"Accept": "text/html"})

    assert private.status_code == 200
    assert private.json()["public_listing"] is False
    assert private.json()["treasurer_npub"] == npub
    assert private.json()["treasurer_pubkey"] == treasurer.public_key_hex()
    assert replay.status_code == 400
    assert "nonce has already been used" in replay.json()["detail"]
    assert "Treasurer Private Credits" not in private_homepage.text
    private_keyset = next(item for item in keysets if item["id"] == cmu["keyset_id"])
    assert private_keyset["public_listing"] is False
    assert private_keyset["active"] is True
    assert published.status_code == 200
    assert published.json()["public_listing"] is True
    assert "Treasurer Private Credits" in public_homepage.text


def test_description_migrates_existing_database(tmp_path) -> None:
    configured = settings(tmp_path)
    with TestClient(create_app(configured)) as client:
        keyset_id = client.get("/v1/keysets").json()["keysets"][0]["id"]
    with sqlite3.connect(configured.database_path) as connection:
        connection.execute("ALTER TABLE cmus DROP COLUMN description")
    with TestClient(create_app(configured)) as client:
        page = client.get(f"/cmus/{keyset_id}")
        assert page.status_code == 200
        assert 'id="cmu-description"' not in page.text
        response = client.post(
            f"/v1/operator/cmus/{keyset_id}/description",
            json={"description": "An existing CMU"},
            headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"},
        )
        assert response.status_code == 200
        assert response.json()["description"] == "An existing CMU"


def test_cmu_description_authority_rendering_and_persistence(tmp_path) -> None:
    configured = settings(tmp_path)
    treasurer = Keys(priv_k="1".zfill(64))
    outsider = Keys(priv_k="2".zfill(64))
    headers = {"Authorization": f"Bearer {OPERATOR_TOKEN}"}
    description = "Meal credits for our community.\n\n<script>alert('x')</script>"
    with TestClient(create_app(configured)) as client:
        commission_and_enable(client)
        client.post("/v1/operator/treasurers", json={"npub": treasurer.public_key_bech32()}, headers=headers)
        grant = client.post("/v1/operator/treasurer-grants", json={"npub": treasurer.public_key_bech32()}, headers=headers).json()
        cmu = client.post("/v1/treasury/cmus", json=build_cmu_create_envelope(
            mint="https://clear.example", grant_id=grant["id"],
            name="Meals", nsec=treasurer.private_key_bech32(),
        )).json()
        assert cmu["description"] == ""
        route = "/v1/treasury/cmus/description"

        def envelope(text, signer=treasurer):
            return build_cmu_description_envelope(
                mint="https://clear.example", nsec=signer.private_key_bech32(),
                keyset_id=cmu["keyset_id"], description=text,
            )

        assert client.post(route, json=envelope("unauthorized", outsider)).status_code == 400
        assert client.post(route, json=envelope("x" * 10001)).status_code == 400
        tampered = envelope("original")
        tampered["payload"]["description"] = "changed"
        assert client.post(route, json=tampered).status_code == 400
        signed = envelope(description)
        result = client.post(route, json=signed)
        assert result.status_code == 200
        assert result.json()["description"] == description
        assert result.json()["unit"] == cmu["unit"]
        assert client.post(route, json=signed).status_code == 400
        page = client.get(f'/cmus/{cmu["keyset_id"]}').text
        assert 'id="cmu-description"' in page
        assert page.index('id="cmu-description"') < page.index('<h2>Supply</h2>')
        assert page.count("Meal credits for our community.") == 1
        assert "Policy-aware supply metrics" not in page
        assert "&lt;script&gt;" in page
        assert "<script>alert('x')</script>" not in page
        operator_route = f'/v1/operator/cmus/{cmu["unit"]}/description'
        assert client.post(operator_route, json={"description": "override"}).status_code != 200
        assert client.post(operator_route, json={"description": "x" * 10001}, headers=headers).status_code == 422
        assert client.post(operator_route, json={"description": "Operator description"}, headers=headers).status_code == 200

    with TestClient(create_app(configured)) as client:
        page = client.get(f'/cmus/{cmu["keyset_id"]}').text
        assert "Operator description" in page
        result = client.post(route, json=envelope(""))
        assert result.status_code == 200
        assert result.json()["description"] == ""
        assert 'id="cmu-description"' not in client.get(f'/cmus/{cmu["keyset_id"]}').text


def test_treasury_cmu_visibility_rejects_unbound_treasurer(tmp_path) -> None:
    configured = settings(tmp_path)
    authorized = Keys(priv_k="1".zfill(64))
    outsider = Keys(priv_k="2".zfill(64))
    with TestClient(create_app(configured)) as client:
        commission_and_enable(client)
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
        cmu = client.post(
            "/v1/treasury/cmus",
            json=build_cmu_create_envelope(
                mint="https://clear.example",
                grant_id=grant["id"],
                name="Protected Credits",
                nsec=authorized.private_key_bech32(),
            ),
        ).json()
        response = client.post(
            "/v1/treasury/cmus/visibility",
            json=build_cmu_visibility_envelope(
                mint="https://clear.example",
                nsec=outsider.private_key_bech32(),
                keyset_id=cmu["keyset_id"],
                public_listing=False,
            ),
    )

    assert response.status_code == 400
    assert "treasurer does not control requested CMU" in response.json()["detail"]


def test_treasury_cmu_info_rejects_unbound_treasurer(tmp_path) -> None:
    configured = settings(tmp_path)
    treasurer = Keys(priv_k="1".zfill(64))
    with TestClient(create_app(configured)) as client:
        response = client.post(
            "/v1/treasury/cmus/info",
            json=build_cmu_info_envelope(
                mint="https://clear.example",
                nsec=treasurer.private_key_bech32(),
                keyset_id="missing-keyset",
            ),
        )

    assert response.status_code == 400
    assert "does not control requested CMU" in response.json()["detail"]


def test_treasurer_can_authorize_quote_for_bound_cmu(tmp_path) -> None:
    configured = settings(tmp_path)
    treasurer = Keys(priv_k="1".zfill(64))
    npub = treasurer.public_key_bech32()
    with TestClient(create_app(configured)) as client:
        commission_and_enable(client)
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
        commission_and_enable(client)
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
        commission_and_enable(client)
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


def test_database_is_bound_to_one_mint_service_identity(tmp_path) -> None:
    with TestClient(create_app(settings(tmp_path))):
        pass

    with sqlite3.connect(tmp_path / "clear.sqlite3") as connection:
        metadata = dict(connection.execute("SELECT key, value FROM mint_metadata"))
    assert metadata["mint_service_npub"] == MINT_SERVICE_NPUB
    assert MINT_SERVICE_NSEC not in metadata.values()

    changed_identity = settings(tmp_path, mint_service_nsec="33" * 32)
    with pytest.raises(RuntimeError, match="service identity does not match"):
        with TestClient(create_app(changed_identity)):
            pass


def test_recorded_mint_service_identity_requires_its_private_key(tmp_path) -> None:
    with TestClient(create_app(settings(tmp_path))):
        pass

    missing_identity = settings(tmp_path, mint_service_nsec=None)
    with pytest.raises(RuntimeError, match="CLEAR_MINT_SERVICE_NSEC is required"):
        with TestClient(create_app(missing_identity)):
            pass


def test_existing_pre_identity_database_can_adopt_its_first_service_key(
    tmp_path,
) -> None:
    with TestClient(create_app(settings(tmp_path, mint_service_nsec=None))):
        pass

    with TestClient(create_app(settings(tmp_path))) as client:
        identity = client.get("/v1/info").json()["service_identity"]

    assert identity["npub"] == MINT_SERVICE_NPUB
    assert identity["state"] == "bootstrapped"


def test_unconfigured_standalone_mint_reports_no_service_identity(tmp_path) -> None:
    with TestClient(
        create_app(settings(tmp_path, mint_service_nsec=None))
    ) as client:
        info = client.get("/v1/info").json()

    assert info["service_identity"] == {
        "npub": None,
        "fips_ipv6_address": None,
        "type": "clear-mint",
        "management": "independent",
        "state": "not-configured",
        "descriptor_event_id": None,
        "operator": None,
    }


def test_mainstay_managed_service_requires_a_private_key(tmp_path) -> None:
    with pytest.raises(ValueError, match="requires CLEAR_MINT_SERVICE_NSEC"):
        settings(
            tmp_path,
            mint_service_nsec=None,
            mint_service_management="mainstay-managed",
        )


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
                "CLEAR_MINT_TITLE=Dotenv Mint",
                "CLEAR_MINT_TAG_LINE=Dotenv tagline",
                "CLEAR_ROOT_AUTHORITY_NPUB=npub1dotenvrootauthority",
                f"CLEAR_MINT_SERVICE_NSEC={MINT_SERVICE_NSEC}",
                "CLEAR_MINT_SERVICE_MANAGEMENT=mainstay-managed",
                "CLEAR_CURRENCY_ALIAS=Dotenv Alias",
                "CLEAR_CURRENCY_UNIT_ALIAS=beans",
                "CLEAR_ROOT_API_ALLOWED_NETWORKS=127.0.0.0/8,172.20.0.0/16",
            ]
        )
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CLEAR_MASTER_SECRET", raising=False)
    monkeypatch.delenv("CLEAR_OPERATOR_TOKEN", raising=False)
    monkeypatch.delenv("CLEAR_DATABASE", raising=False)
    monkeypatch.delenv("CLEAR_CURRENCY_NAME", raising=False)
    monkeypatch.delenv("CLEAR_MINT_TITLE", raising=False)
    monkeypatch.delenv("CLEAR_MINT_TAG_LINE", raising=False)
    monkeypatch.delenv("CLEAR_ROOT_AUTHORITY_NPUB", raising=False)
    monkeypatch.delenv("CLEAR_MINT_SERVICE_NSEC", raising=False)
    monkeypatch.delenv("CLEAR_MINT_SERVICE_MANAGEMENT", raising=False)
    monkeypatch.delenv("CLEAR_CURRENCY_ALIAS", raising=False)
    monkeypatch.delenv("CLEAR_CURRENCY_UNIT_ALIAS", raising=False)
    monkeypatch.delenv("CLEAR_ROOT_API_ALLOWED_NETWORKS", raising=False)

    settings = Settings.from_env()

    assert settings.master_secret == MASTER_SECRET
    assert settings.operator_token == OPERATOR_TOKEN
    assert settings.database_path == database_path
    assert settings.currency_name == "Dotenv Credits"
    assert settings.mint_title == "Dotenv Mint"
    assert settings.mint_tag_line == "Dotenv tagline"
    assert settings.root_authority_npub == "npub1dotenvrootauthority"
    assert settings.mint_service_npub == MINT_SERVICE_NPUB
    assert settings.mint_service_management == "mainstay-managed"
    assert settings.currency_alias == "Dotenv Alias"
    assert settings.currency_unit_alias == "beans"
    assert settings.root_api_allowed_networks == "127.0.0.0/8,172.20.0.0/16"


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
