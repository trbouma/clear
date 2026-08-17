"""FastAPI protocol surface for the Clear mint."""

from __future__ import annotations

import hmac
from contextlib import asynccontextmanager
from ipaddress import ip_address

from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from clear import __version__
from clear.config import Settings
from clear.crypto import Keyset
from clear.models import (
    CheckStateRequest,
    MintQuoteRequest,
    MintRequest,
    RetireRequest,
    SwapRequest,
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
    store = Store(configured.database_path, keyset)

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

    @app.get("/")
    async def information():
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

    def keyset_response():
        return {
            "id": keyset.id,
            "unit": keyset.unit,
            "active": True,
            "input_fee_ppk": 0,
            "final_expiry": None,
            "keys": {str(amount): key for amount, key in keyset.public_keys.items()},
        }

    @app.get("/v1/keys")
    async def keys():
        return {"keysets": [keyset_response()]}

    @app.get("/v1/keys/{keyset_id}")
    async def keys_by_id(keyset_id: str):
        if keyset_id != keyset.id:
            return _protocol_error("keyset not found", 10001)
        return {"keysets": [keyset_response()]}

    @app.get("/v1/keysets")
    async def keysets():
        response = keyset_response()
        response.pop("keys")
        return {"keysets": [response]}

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
            amount = store.retire(request.inputs, request.memo)
        except ClearError as exc:
            return _protocol_error(str(exc), 13000)
        return {"status": "RETIRED", "amount": amount, "unit": keyset.unit}

    @app.get("/v1/operator/summary")
    async def operator_summary(
        request: Request,
        authorization: str | None = Header(default=None),
    ):
        if error := operator_access_error(request, authorization):
            return error
        return store.summary()

    return app
