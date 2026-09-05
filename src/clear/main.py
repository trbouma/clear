"""FastAPI protocol surface for the Clear mint."""

from __future__ import annotations

import hmac
from contextlib import asynccontextmanager
from ipaddress import ip_address

from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from clear import __version__
from clear.commissioning import configuration_fingerprint, run_verification
from clear.config import Settings
from clear.crypto import Keyset
from clear.homepage import render_homepage
from clear.models import (
    CheckStateRequest,
    CMUCreateRequest,
    CMULabelRequest,
    MintQuoteRequest,
    MintRequest,
    RetireRequest,
    SwapRequest,
    TreasurerGrantRequest,
    TreasurerRequest,
    TreasuryDisableRequest,
    TreasuryEnvelopeRequest,
)
from clear.store import ClearError, Store


def _protocol_error(detail: str, code: int = 10000) -> JSONResponse:
    return JSONResponse({"detail": detail, "code": code}, status_code=400)


def create_app(settings: Settings | None = None) -> FastAPI:
    configured = settings or Settings.from_env()
    keyset = Keyset(
        configured.master_secret,
        max_order=configured.max_order,
        root_authority_npub=configured.root_authority_npub,
    )
    store = Store(
        configured.database_path,
        keyset,
        key_encryption_key=configured.key_encryption_key or configured.master_secret,
        legacy_friendly_name=(
            configured.currency_alias
            or f"{configured.currency_name} ({keyset.unit})"
        ),
        legacy_friendly_unit_alias=configured.currency_unit_alias,
        configuration_fingerprint=configuration_fingerprint(
            configured,
            keyset,
            software_version=__version__,
        ),
        software_version=__version__,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        store.initialize()
        yield

    app = FastAPI(
        title="Clear",
        description=(
            "An experimental Cashu mint for organization-defined Clear Mint Units "
            "without Lightning settlement."
        ),
        version=__version__,
        lifespan=lifespan,
    )
    app.state.settings = configured
    app.state.keyset = keyset
    app.state.store = store
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        max_age=86400,
    )

    def request_is_loopback(request: Request) -> bool:
        if request.client is None:
            return False
        host = request.client.host.rstrip(".").lower()
        if host == "localhost":
            return True
        try:
            return ip_address(host).is_loopback
        except ValueError:
            return False

    def operator_access_error(
        request: Request, authorization: str | None
    ) -> JSONResponse | None:
        if configured.root_api_loopback_only and not request_is_loopback(request):
            return JSONResponse(
                {"detail": "operator API requires loopback access"},
                status_code=403,
            )
        scheme, _, token = (authorization or "").partition(" ")
        if scheme.lower() != "bearer" or not hmac.compare_digest(
            token, configured.operator_token
        ):
            return JSONResponse(
                {"detail": "operator authorization required"}, status_code=401
            )
        return None

    def policy_response():
        return {
            "mode": "root-bootstrap",
            "root_authority_npub": configured.root_authority_npub,
            "enforced": False,
        }

    def currency_alias_response():
        alias_base = configured.currency_alias or configured.currency_name
        alias = (
            configured.currency_alias
            or f"{configured.currency_name} ({keyset.unit})"
        )
        return {
            "friendly_alias": alias,
            "friendly_unit_alias": configured.currency_unit_alias,
            "friendly_alias_key": (
                f"{alias_base.lower().replace(' ', '-')}:"
                f"{keyset.fingerprint}"
            ),
            "identity_note": (
                "Suggested wallet label only; balances must bind to mint URL, "
                "unit, and keyset id."
            ),
        }

    def information_response():
        return {
            "name": "Clear",
            "version": __version__,
            "description": "Organization-defined Clear Mint Units",
            "currency": {
                "name": configured.currency_name,
                "display_unit": "CMU",
                "protocol_unit": keyset.unit,
                "keyset_fingerprint": keyset.fingerprint,
                "keyset_id": keyset.id,
                **currency_alias_response(),
            },
            "policy": policy_response(),
            "warning": "Developer-stage software; not security reviewed.",
        }

    @app.get("/", response_model=None)
    async def information(request: Request):
        accept = request.headers.get("accept", "").lower()
        if "text/html" in accept:
            return HTMLResponse(
                render_homepage(
                    version=__version__,
                    mint_url=configured.mint_url,
                    currency_name=configured.currency_name,
                    currency_alias=configured.currency_alias,
                    currency_unit_alias=configured.currency_unit_alias,
                    protocol_unit=keyset.unit,
                    keyset_id=keyset.id,
                    root_authority_configured=(
                        configured.root_authority_npub is not None
                    ),
                )
            )
        return information_response()

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/v1/info")
    async def mint_info():
        return {
            "name": "Clear",
            "version": __version__,
            "mint_url": configured.mint_url,
            "description": f"{configured.currency_name} issued as Clear ecash",
            "currency": {
                "name": configured.currency_name,
                "display_unit": "CMU",
                "unit": keyset.unit,
                "keyset_fingerprint": keyset.fingerprint,
                "keyset_id": keyset.id,
                **currency_alias_response(),
            },
            "policy": policy_response(),
            "nuts": {
                "4": {
                    "methods": [
                        {
                            "method": "clear",
                            "unit": keyset.unit,
                            "method_name": "Treasurer authorization",
                            "min_amount": 1,
                            "max_amount": 2 ** (configured.max_order + 1) - 1,
                        }
                    ],
                    "disabled": False,
                },
                "7": {"supported": True},
            },
        }

    @app.get("/v1/keys")
    async def keys():
        return {"keysets": store.keyset_responses(include_keys=True)}

    @app.get("/v1/keys/{keyset_id}")
    async def keys_by_id(keyset_id: str):
        try:
            response = store.keyset_response(keyset_id, include_keys=True)
        except ClearError:
            return _protocol_error("keyset not found", 10001)
        return {"keysets": [response]}

    @app.get("/v1/keysets")
    async def keysets():
        return {"keysets": store.keyset_responses(include_keys=False)}

    @app.post("/v1/mint/quote/clear")
    async def create_mint_quote(request: MintQuoteRequest):
        max_amount = 2 ** (configured.max_order + 1) - 1
        if request.amount > max_amount:
            return _protocol_error(
                f"quote amount exceeds the configured maximum of {max_amount}",
                11000,
            )
        try:
            return store.create_quote(request.amount, request.unit, request.memo)
        except ClearError as exc:
            return _protocol_error(str(exc), 11000)

    @app.get("/v1/mint/quote/clear/{quote_id}")
    async def get_mint_quote(quote_id: str):
        try:
            return store.get_quote(quote_id)
        except ClearError as exc:
            return _protocol_error(str(exc), 11001)

    @app.post("/v1/operator/quotes/{quote_id}/authorize")
    async def authorize_mint_quote(
        quote_id: str,
        request: Request,
        authorization: str | None = Header(default=None),
    ):
        if error := operator_access_error(request, authorization):
            return error
        try:
            return store.authorize_quote(quote_id)
        except ClearError as exc:
            return _protocol_error(str(exc), 11001)

    @app.post("/v1/mint/clear")
    async def mint(request: MintRequest):
        try:
            signatures = store.issue(request.quote, request.outputs)
        except ClearError as exc:
            return _protocol_error(str(exc), 11002)
        return {"signatures": signatures}

    @app.post("/v1/swap")
    async def swap(request: SwapRequest):
        try:
            signatures = store.swap(request.inputs, request.outputs)
        except ClearError as exc:
            return _protocol_error(str(exc), 12000)
        return {"signatures": signatures}

    @app.post("/v1/checkstate")
    async def check_state(request: CheckStateRequest):
        return {"states": store.states(request.Ys)}

    @app.post("/v1/operator/retire")
    async def retire(
        request: RetireRequest,
        http_request: Request,
        authorization: str | None = Header(default=None),
    ):
        if error := operator_access_error(http_request, authorization):
            return error
        try:
            retired = store.retire(request.inputs, request.memo)
        except ClearError as exc:
            return _protocol_error(str(exc), 13000)
        return {"status": "RETIRED", **retired}

    @app.get("/v1/operator/summary")
    async def operator_summary(
        request: Request,
        authorization: str | None = Header(default=None),
    ):
        if error := operator_access_error(request, authorization):
            return error
        return store.summary()

    @app.get("/v1/operator/treasury")
    async def treasury_status(
        request: Request,
        authorization: str | None = Header(default=None),
    ):
        if error := operator_access_error(request, authorization):
            return error
        return store.commissioning_status()

    @app.post("/v1/operator/commissioning/verify")
    async def verify_commissioning(
        request: Request,
        authorization: str | None = Header(default=None),
    ):
        if error := operator_access_error(request, authorization):
            return error
        try:
            return run_verification(store, mint_url=configured.mint_url)
        except ClearError as exc:
            return _protocol_error(str(exc), 16000)

    @app.post("/v1/operator/treasury/enable")
    async def enable_treasury(
        request: Request,
        authorization: str | None = Header(default=None),
    ):
        if error := operator_access_error(request, authorization):
            return error
        try:
            return store.enable_treasury()
        except ClearError as exc:
            return _protocol_error(str(exc), 16001)

    @app.post("/v1/operator/treasury/disable")
    async def disable_treasury(
        body: TreasuryDisableRequest,
        request: Request,
        authorization: str | None = Header(default=None),
    ):
        if error := operator_access_error(request, authorization):
            return error
        try:
            return store.disable_treasury(body.reason)
        except ClearError as exc:
            return _protocol_error(str(exc), 16002)

    @app.get("/v1/operator/treasurers")
    async def list_treasurers(
        request: Request,
        authorization: str | None = Header(default=None),
    ):
        if error := operator_access_error(request, authorization):
            return error
        return store.list_treasurers()

    @app.post("/v1/operator/treasurers")
    async def add_treasurer(
        body: TreasurerRequest,
        request: Request,
        authorization: str | None = Header(default=None),
    ):
        if error := operator_access_error(request, authorization):
            return error
        try:
            return store.add_treasurer(body.npub)
        except ClearError as exc:
            return _protocol_error(str(exc), 14000)

    @app.get("/v1/operator/treasurer-grants")
    async def list_treasurer_grants(
        request: Request,
        authorization: str | None = Header(default=None),
    ):
        if error := operator_access_error(request, authorization):
            return error
        return store.list_treasurer_grants()

    @app.post("/v1/operator/treasurer-grants")
    async def grant_treasurer(
        body: TreasurerGrantRequest,
        request: Request,
        authorization: str | None = Header(default=None),
    ):
        if error := operator_access_error(request, authorization):
            return error
        try:
            return store.grant_treasurer(body.npub)
        except ClearError as exc:
            return _protocol_error(str(exc), 14001)

    @app.get("/v1/operator/cmus")
    async def list_cmus(
        request: Request,
        authorization: str | None = Header(default=None),
    ):
        if error := operator_access_error(request, authorization):
            return error
        return store.list_cmus()

    @app.post("/v1/operator/cmus")
    async def create_cmu(
        body: CMUCreateRequest,
        request: Request,
        authorization: str | None = Header(default=None),
    ):
        if error := operator_access_error(request, authorization):
            return error
        try:
            return store.create_cmu(
                body.grant_id,
                friendly_name=body.name,
                friendly_unit_alias=body.unit_alias,
            )
        except ClearError as exc:
            return _protocol_error(str(exc), 15000)

    @app.post("/v1/operator/cmus/{unit_or_keyset_id}/label")
    async def label_cmu(
        unit_or_keyset_id: str,
        body: CMULabelRequest,
        request: Request,
        authorization: str | None = Header(default=None),
    ):
        if error := operator_access_error(request, authorization):
            return error
        try:
            return store.update_cmu_label(
                unit_or_keyset_id,
                friendly_name=body.name,
                friendly_unit_alias=body.unit_alias,
            )
        except ClearError as exc:
            return _protocol_error(str(exc), 15004)

    @app.post("/v1/treasury/cmus")
    async def create_cmu_from_treasury(body: TreasuryEnvelopeRequest):
        try:
            store.require_treasury_enabled()
            return store.create_cmu_from_treasury_envelope(
                body.model_dump(),
                mint_url=configured.mint_url,
            )
        except ClearError as exc:
            return _protocol_error(str(exc), 15001)

    @app.post("/v1/treasury/cmus/info")
    async def cmu_info_from_treasury(body: TreasuryEnvelopeRequest):
        try:
            return store.cmu_info_from_treasury_envelope(
                body.model_dump(),
                mint_url=configured.mint_url,
            )
        except ClearError as exc:
            return _protocol_error(str(exc), 15002)

    @app.post("/v1/treasury/cmus/summary")
    async def cmu_summary_from_treasury(body: TreasuryEnvelopeRequest):
        try:
            return store.cmu_summary_from_treasury_envelope(
                body.model_dump(),
                mint_url=configured.mint_url,
            )
        except ClearError as exc:
            return _protocol_error(str(exc), 15005)

    @app.post("/v1/treasury/quotes/{quote_id}/authorize")
    async def authorize_quote_from_treasury(
        quote_id: str,
        body: TreasuryEnvelopeRequest,
    ):
        envelope = body.model_dump()
        envelope["payload"]["quote_id"] = quote_id
        try:
            store.require_treasury_enabled()
            return store.authorize_quote_from_treasury_envelope(
                envelope,
                mint_url=configured.mint_url,
            )
        except ClearError as exc:
            return _protocol_error(str(exc), 15003)

    return app
