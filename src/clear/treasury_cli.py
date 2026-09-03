"""Treasurer-side CLI for signed Clear treasury actions."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

from clear.root_delivery import (
    DeliveryError,
    deliver_clear_token,
    discover_clear_support,
)
from clear.root_wallet import (
    deposit_issue,
    export_token,
    load_wallet,
    replace_selected_with_change,
    select_proofs_for_amount,
    wallet_summary,
)
from clear.treasury import (
    TreasuryError,
    issue_treasury_units,
    request_json,
    swap_token_for_amount,
)
from clear.treasury_auth import (
    TreasuryAuthError,
    build_cmu_create_envelope,
    build_cmu_info_envelope,
    npub_from_nsec,
)

DEFAULT_TREASURY_WALLET_BASE = Path("~/.clear/treasury-wallets").expanduser()


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, indent=2))


def _treasurer_nsec(args) -> str:
    nsec = args.nsec or os.getenv("CLEAR_TREASURER_NSEC")
    if not nsec:
        raise TreasuryError("treasurer nsec must be supplied with --nsec")
    return nsec


def _wallet_path(args, nsec: str | None = None) -> Path:
    if args.wallet:
        return Path(args.wallet).expanduser()
    if env_path := os.getenv("CLEAR_TREASURY_WALLET"):
        return Path(env_path).expanduser()
    if nsec is None:
        nsec = _treasurer_nsec(args)
    mint = args.mint.rstrip("/")
    host = urlparse(mint).netloc or mint.replace("://", "_")
    treasurer_npub = npub_from_nsec(nsec)
    digest = hashlib.sha256(mint.encode()).hexdigest()[:12]
    return DEFAULT_TREASURY_WALLET_BASE / f"{host}-{digest}" / f"{treasurer_npub}.json"


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


def issue(args) -> int:
    nsec = _treasurer_nsec(args)
    issued = issue_treasury_units(
        args.mint.rstrip("/"),
        nsec,
        args.amount,
        memo=args.memo,
        lifetime_seconds=args.lifetime,
    )
    if not args.to_token:
        summary = deposit_issue(issued, _wallet_path(args, nsec))
        issued = {
            key: value
            for key, value in issued.items()
            if key not in {"token", "proofs"}
        }
        issued["wallet"] = summary
    _print_json(
        {
            **issued,
            "treasurer_npub": npub_from_nsec(nsec),
        }
    )
    return 0


def _cmu_info(mint: str, nsec: str, lifetime_seconds: int) -> dict:
    envelope = build_cmu_info_envelope(
        mint=mint,
        nsec=nsec,
        lifetime_seconds=lifetime_seconds,
    )
    return request_json(mint, "POST", "/v1/treasury/cmus/info", envelope)


def _export_or_swap(
    amount: int,
    wallet_path: Path,
    *,
    mint_url: str,
    unit: str,
    memo: str | None = None,
) -> dict:
    try:
        return export_token(amount, wallet_path, memo=memo, remove=False)
    except ValueError as exc:
        if str(exc) != "wallet cannot export exact amount with current proof set":
            raise

    selected = select_proofs_for_amount(amount, wallet_path)
    if selected["mint"] != mint_url or selected["unit"] != unit:
        raise TreasuryError("selected wallet proofs are not for this treasurer CMU")
    swapped = swap_token_for_amount(
        mint_url,
        selected["proofs"],
        amount,
        unit=unit,
        memo=memo,
    )
    replacement_proofs = [*swapped["proofs"], *swapped["change_proofs"]]
    replace_selected_with_change(
        selected["amount"],
        wallet_path,
        change={
            "mint": swapped["mint"],
            "unit": unit,
            "quote": None,
            "amount": selected["amount"],
            "memo": memo,
            "proofs": replacement_proofs,
        },
    )
    return export_token(amount, wallet_path, memo=memo, remove=False)


def send(args) -> int:
    nsec = _treasurer_nsec(args)
    mint = args.mint.rstrip("/")
    cmu = _cmu_info(mint, nsec, args.lifetime)
    discovery = discover_clear_support(
        args.address,
        mint_url=mint,
        unit=cmu["unit"],
    )
    if not discovery["supported"]:
        raise DeliveryError("recipient does not advertise compatible Clear support")
    wallet_path = _wallet_path(args, nsec)
    pending = _export_or_swap(
        args.amount,
        wallet_path,
        mint_url=mint,
        unit=cmu["unit"],
        memo=args.memo,
    )
    delivery = deliver_clear_token(
        discovery,
        token=pending["token"],
        amount=args.amount,
        sender_secret=args.sender_nsec,
        memo=args.memo,
        relays=args.relay,
        expiration=args.expiration,
    )
    withdrawn = export_token(args.amount, wallet_path, memo=args.memo, remove=True)
    _print_json(
        {
            **withdrawn,
            **delivery,
            "treasurer_npub": npub_from_nsec(nsec),
        }
    )
    return 0


def wallet_balance(args) -> int:
    nsec = _treasurer_nsec(args)
    path = _wallet_path(args, nsec)
    _print_json(
        {
            "treasurer_npub": npub_from_nsec(nsec),
            **wallet_summary(load_wallet(path), path),
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
    result.add_argument(
        "--wallet",
        default=None,
        help=(
            "Treasurer wallet JSON path. Defaults to CLEAR_TREASURY_WALLET or "
            "~/.clear/treasury-wallets/<mint>/<treasurer-npub>.json."
        ),
    )

    subcommands = result.add_subparsers(dest="command", required=True)
    issue_parser = subcommands.add_parser(
        "issue",
        help="Issue CMU controlled by the treasurer nsec into the treasury wallet.",
    )
    issue_parser.add_argument("amount", type=int, help="Amount of CMU to issue.")
    issue_parser.add_argument("--memo", default=None, help="Optional quote memo.")
    issue_parser.add_argument(
        "--to-token",
        action="store_true",
        help=(
            "Encode the issued CMU as a Cashu token immediately instead of "
            "storing its proofs in the treasury wallet."
        ),
    )
    issue_parser.add_argument(
        "--lifetime",
        type=int,
        default=300,
        help="Signed request lifetime in seconds.",
    )
    issue_parser.set_defaults(handler=issue)

    send_parser = subcommands.add_parser(
        "send",
        help="Withdraw and deliver a token from the treasury wallet.",
    )
    send_parser.add_argument("amount", type=int)
    send_parser.add_argument("address")
    send_parser.add_argument("--memo", default=None)
    send_parser.add_argument(
        "--sender-nsec",
        default=None,
        help=(
            "Optional Nostr sender nsec for delivery. Defaults to an ephemeral "
            "sender key."
        ),
    )
    send_parser.add_argument(
        "--relay",
        action="append",
        default=None,
        help="Relay to publish to. Repeatable. Defaults to recipient relay hints.",
    )
    send_parser.add_argument(
        "--expiration",
        type=int,
        default=None,
        help="Optional Unix timestamp for the gift-wrap expiration tag.",
    )
    send_parser.add_argument(
        "--lifetime",
        type=int,
        default=300,
        help="Signed request lifetime in seconds.",
    )
    send_parser.set_defaults(handler=send)

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

    wallet_parser = subcommands.add_parser(
        "wallet",
        help="Manage local treasury wallet.",
    )
    wallet_subcommands = wallet_parser.add_subparsers(
        dest="wallet_command",
        required=True,
    )
    balance_parser = wallet_subcommands.add_parser(
        "balance",
        help="Show local treasury wallet balances.",
    )
    balance_parser.set_defaults(handler=wallet_balance)
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
