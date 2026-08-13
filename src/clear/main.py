"""FastAPI protocol surface for the Clear mint."""

from __future__ import annotations

import hmac
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header
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
    )
    store = Store(configured.database_path, keyset)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        store.initialize()
        yield

    app = FastAPI(
        title="Clear",
        description=(
            "An experimental Cashu mint for organization-defined points "
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

    def operator_authorized(authorization: str | None) -> bool:
        scheme, _, token = (authorization or "").partition(" ")
        return scheme.lower() == "bearer" and hmac.compare_digest(
            token, configured.operator_token
        )

    @app.get("/")
    async def information():
        return {
            "name": "Clear",
            "version": __version__,
            "description": "Organization-defined Cashu points",
            "currency": {
                "name": configured.currency_name,
                "display_unit": "pts",
                "protocol_unit": keyset.unit,
                "keyset_fingerprint": keyset.fingerprint,
                "keyset_id": keyset.id,
            },
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
            "description": f"{configured.currency_name} issued as Clear ecash",
            "currency": {
                "name": configured.currency_name,
                "display_unit": "pts",
                "unit": keyset.unit,
                "keyset_fingerprint": keyset.fingerprint,
                "keyset_id": keyset.id,
            },
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
        quote_id: str, authorization: str | None = Header(default=None)
    ):
        if not operator_authorized(authorization):
            return JSONResponse(
                {"detail": "operator authorization required"}, status_code=401
            )
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
        authorization: str | None = Header(default=None),
    ):
        if not operator_authorized(authorization):
            return JSONResponse(
                {"detail": "operator authorization required"}, status_code=401
            )
        try:
            amount = store.retire(request.inputs, request.memo)
        except ClearError as exc:
            return _protocol_error(str(exc), 13000)
        return {"status": "RETIRED", "amount": amount, "unit": keyset.unit}

    @app.get("/v1/operator/summary")
    async def operator_summary(
        authorization: str | None = Header(default=None),
    ):
        if not operator_authorized(authorization):
            return JSONResponse(
                {"detail": "operator authorization required"}, status_code=401
            )
        return store.summary()

    return app
