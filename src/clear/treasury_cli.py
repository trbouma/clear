"""Treasurer-side CLI for signed Clear treasury actions."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from clear.treasury import TreasuryError, request_json
from clear.treasury_auth import (
    TreasuryAuthError,
    build_cmu_create_envelope,
    build_cmu_info_envelope,
    npub_from_nsec,
)


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, indent=2))


def _treasurer_nsec(args) -> str:
    nsec = args.nsec or os.getenv("CLEAR_TREASURER_NSEC")
    if not nsec:
        raise TreasuryError("treasurer nsec must be supplied with --nsec")
    return nsec


def cmu_create(args) -> int:
    nsec = _treasurer_nsec(args)
    mint = args.mint.rstrip("/")
    envelope = build_cmu_create_envelope(
        mint=mint,
        grant_id=args.grant_id,
        name=args.name,
        nsec=nsec,
        lifetime_seconds=args.lifetime,
    )
    result = request_json(mint, "POST", "/v1/treasury/cmus", envelope)
    _print_json(
        {
            **result,
            "treasurer_npub": npub_from_nsec(nsec),
        }
    )
    return 0


def cmu_info(args) -> int:
    nsec = _treasurer_nsec(args)
    mint = args.mint.rstrip("/")
    envelope = build_cmu_info_envelope(
        mint=mint,
        nsec=nsec,
        lifetime_seconds=args.lifetime,
    )
    result = request_json(mint, "POST", "/v1/treasury/cmus/info", envelope)
    _print_json(
        {
            **result,
            "treasurer_npub": npub_from_nsec(nsec),
        }
    )
    return 0


def parser(*, prog: str = "clear-treasury") -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog=prog,
        description=(
            "Clear treasurer CLI. This command signs requests with a treasurer "
            "nsec and sends them to public treasury endpoints."
        ),
    )
    result.add_argument(
        "--mint",
        required=True,
        help="Public Clear mint URL, for example https://clear.example.",
    )
    result.add_argument(
        "--nsec",
        default=None,
        help="Treasurer nsec. Defaults to CLEAR_TREASURER_NSEC.",
    )

    subcommands = result.add_subparsers(dest="command", required=True)
    cmu_parser = subcommands.add_parser("cmu", help="Treasurer CMU actions.")
    cmu_subcommands = cmu_parser.add_subparsers(dest="cmu_command", required=True)
    cmu_create_parser = cmu_subcommands.add_parser(
        "create",
        help="Consume a grant by signing a CMU creation request.",
    )
    cmu_create_parser.add_argument("grant_id")
    cmu_create_parser.add_argument("--name", default=None, help="Friendly CMU name.")
    cmu_create_parser.add_argument(
        "--lifetime",
        type=int,
        default=300,
        help="Signed request lifetime in seconds.",
    )
    cmu_create_parser.set_defaults(handler=cmu_create)
    cmu_info_parser = cmu_subcommands.add_parser(
        "info",
        help="Show the active CMU controlled by the treasurer nsec.",
    )
    cmu_info_parser.add_argument(
        "--lifetime",
        type=int,
        default=300,
        help="Signed request lifetime in seconds.",
    )
    cmu_info_parser.set_defaults(handler=cmu_info)
    return result


def main() -> int:
    load_dotenv(override=False)
    program = Path(sys.argv[0]).name or "clear-treasury"
    args = parser(prog=program).parse_args()
    try:
        return args.handler(args)
    except (TreasuryAuthError, TreasuryError, ValueError) as exc:
        print(f"{program} {args.command} failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
