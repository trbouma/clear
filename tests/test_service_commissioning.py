from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from stroma import Event, Keys

from clear.config import Settings
from clear.main import create_app
from clear.service_commissioning import (
    ADDRESSABLE_APPLICATION_EVENT_KIND,
    ATTESTATION_SCHEMA,
    SERVICE_TYPE,
    canonical_json,
    create_commissioning_request,
    create_service_descriptor,
    verify_operator_attestation,
    verify_service_descriptor,
)
from clear.store import ClearError

SERVICE_NSEC = "22" * 32
SERVICE_KEYS = Keys(priv_k=SERVICE_NSEC)
SERVICE_NPUB = SERVICE_KEYS.public_key_bech32()
OPERATOR_KEYS = Keys(priv_k="33" * 32)
OPERATOR_NPUB = OPERATOR_KEYS.public_key_bech32()
NOW = 1_788_700_000


def operator_attestation(request_data: dict, *, keys=OPERATOR_KEYS) -> dict:
    request = Event.load(request_data, validate=True)
    assert request is not None
    issued_at = request.created_at + 1
    content = {
        "action": "authorize",
        "commissioning_request": request.id,
        "installation": keys.public_key_hex(),
        "issued_at": issued_at,
        "management": "mainstay-managed",
        "previous": None,
        "relationship": "operates",
        "schema": ATTESTATION_SCHEMA,
        "schema_version": 1,
        "sequence": 1,
        "service": {
            "pubkey": SERVICE_KEYS.public_key_hex(),
            "type": SERVICE_TYPE,
        },
    }
    event = Event(
        kind=ADDRESSABLE_APPLICATION_EVENT_KIND,
        content=canonical_json(content),
        tags=[
            [
                "d",
                f"{ATTESTATION_SCHEMA}:{SERVICE_KEYS.public_key_hex()}",
            ],
            ["p", SERVICE_KEYS.public_key_hex(), "", "service"],
            ["e", request.id, "", "commissioning-request"],
            ["t", "mainstay-service-operator"],
            ["service-type", SERVICE_TYPE],
        ],
        created_at=issued_at,
    )
    event.sign(keys)
    return event.data()


def commissioning_request() -> dict:
    return create_commissioning_request(
        SERVICE_NSEC,
        OPERATOR_NPUB,
        "mainstay-managed",
        now=NOW,
        nonce="44" * 32,
    )


def test_reciprocal_commissioning_evidence_verifies() -> None:
    request = commissioning_request()
    attestation = operator_attestation(request)

    verified = verify_operator_attestation(
        request,
        attestation,
        service_npub=SERVICE_NPUB,
        management="mainstay-managed",
        now=NOW + 2,
    )
    descriptor = create_service_descriptor(
        SERVICE_NSEC,
        attestation,
        management="mainstay-managed",
        now=NOW + 2,
    )
    verified_descriptor = verify_service_descriptor(
        descriptor,
        attestation,
        service_npub=SERVICE_NPUB,
        management="mainstay-managed",
    )

    assert verified.operator_npub == OPERATOR_NPUB
    assert verified.request.id == request["id"]
    assert verified.attestation.id == attestation["id"]
    assert verified_descriptor.id == descriptor["id"]


def test_attestation_from_another_operator_is_rejected() -> None:
    request = commissioning_request()
    attestation = operator_attestation(request, keys=Keys(priv_k="55" * 32))

    with pytest.raises(ClearError, match="requested operator"):
        verify_operator_attestation(
            request,
            attestation,
            service_npub=SERVICE_NPUB,
            management="mainstay-managed",
            now=NOW + 2,
        )


def test_attestation_for_another_service_is_rejected() -> None:
    request = commissioning_request()
    attestation = operator_attestation(request)
    event = Event.load(attestation)
    assert event is not None
    content = json.loads(event.content)
    content["service"]["pubkey"] = Keys(priv_k="66" * 32).public_key_hex()
    event.content = canonical_json(content)
    event.sign(OPERATOR_KEYS)

    with pytest.raises(ClearError, match="does not match the request"):
        verify_operator_attestation(
            request,
            event.data(),
            service_npub=SERVICE_NPUB,
            management="mainstay-managed",
            now=NOW + 2,
        )


def test_expired_request_is_rejected() -> None:
    request = commissioning_request()
    attestation = operator_attestation(request)

    with pytest.raises(ClearError, match="expired"):
        verify_operator_attestation(
            request,
            attestation,
            service_npub=SERVICE_NPUB,
            management="mainstay-managed",
            now=NOW + 24 * 60 * 60 + 1,
        )


def test_historical_attestation_remains_verifiable_after_request_expiry() -> None:
    request = commissioning_request()
    attestation = operator_attestation(request)

    verified = verify_operator_attestation(
        request,
        attestation,
        service_npub=SERVICE_NPUB,
        management="mainstay-managed",
        now=NOW + 365 * 24 * 60 * 60,
        require_current_request=False,
    )

    assert verified.attestation.id == attestation["id"]


def test_clear_api_commissions_and_retains_service_evidence(tmp_path) -> None:
    configured = Settings(
        database_path=tmp_path / "clear.sqlite3",
        master_secret="11" * 32,
        operator_token="operator-token-that-is-long-enough",
        mint_service_nsec=SERVICE_NSEC,
        mint_service_management="mainstay-managed",
        root_api_loopback_only=False,
    )
    headers = {"Authorization": "Bearer operator-token-that-is-long-enough"}

    with TestClient(create_app(configured)) as client:
        initial = client.get("/v1/info").json()["service_identity"]
        requested = client.post(
            "/v1/operator/service/request",
            json={"operator_npub": OPERATOR_NPUB},
            headers=headers,
        )
        assert requested.status_code == 200, requested.json()
        request_event = requested.json()["commissioning_request"]
        attestation = operator_attestation(request_event)
        commissioned = client.post(
            "/v1/operator/service/commission",
            json={"event": attestation},
            headers=headers,
        )
        verified = client.post(
            "/v1/operator/service/verify",
            headers=headers,
        )
        public = client.get("/v1/service-identity")

    assert initial["state"] == "bootstrapped"
    assert initial["operator"] is None
    assert commissioned.status_code == 200, commissioned.json()
    assert commissioned.json()["service_identity"]["state"] == "commissioned"
    assert verified.status_code == 200, verified.json()
    assert verified.json()["operator_npub"] == OPERATOR_NPUB
    assert public.json()["service_identity"]["operator"]["status"] == "verified"
    assert public.json()["evidence"]["operator_attestation"]["id"] == attestation["id"]

    with TestClient(create_app(configured)) as client:
        recovered = client.get("/v1/service-identity").json()
        reverified = client.post(
            "/v1/operator/service/verify",
            headers=headers,
        )

    assert recovered["service_identity"]["state"] == "commissioned"
    assert reverified.status_code == 200
