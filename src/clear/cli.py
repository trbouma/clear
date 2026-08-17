"""Command-line entry point for Clear."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

import uvicorn

from clear.config import Settings
from clear.main import create_app


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="clear",
        description="Run an organization-defined Clear Mint Unit mint.",
    )
    result.add_argument("--host", default="127.0.0.1")
    result.add_argument("--port", type=int, default=3338)
    result.add_argument("--database", type=Path)
    result.add_argument("--currency-name")
    result.add_argument("--mint-url")
    result.add_argument("--log-level", default="info")
    return result


def main() -> None:
    args = parser().parse_args()
    settings = Settings.from_env()
    overrides = {}
    if args.database is not None:
        overrides["database_path"] = args.database
    if args.currency_name is not None:
        overrides["currency_name"] = args.currency_name
    if args.mint_url is not None:
        overrides["mint_url"] = args.mint_url.rstrip("/")
    else:
        overrides["mint_url"] = f"http://{args.host}:{args.port}"
    configured = replace(settings, **overrides)
    uvicorn.run(
        create_app(configured),
        host=args.host,
        port=args.port,
        log_level=args.log_level,
    )
