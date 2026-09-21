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

from clear.cmu_description import add_description_arguments, read_description
from clear.root_delivery import (
    DeliveryError,
    deliver_clear_token,
    discover_clear_support,
    mint_has_public_route,
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
    build_cmu_summary_envelope,
    build_cmu_visibility_envelope,
    build_cmu_description_envelope,
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


def _resolve_keyset_id(mint: str, args) -> str:
    keyset_id = getattr(args, "keyset_id", None)
    if keyset_id:
        return keyset_id
    cmu_id = getattr(args, "cmu_id", None)
    if not cmu_id:
        raise TreasuryError("treasurer CMU selection requires --keyset-id or --cmu-id")
    response = request_json(mint, "GET", "/v1/keysets")
    matches = [
        item
        for item in response.get("keysets") or []
        if item.get("unit") == cmu_id
    ]
    if not matches:
        raise TreasuryError(f"CMU was not found: {cmu_id}")
    if len(matches) > 1:
        raise TreasuryError(f"CMU matched multiple keysets: {cmu_id}")
    resolved = matches[0].get("id")
    if not isinstance(resolved, str) or not resolved:
        raise TreasuryError(f"CMU keyset id is missing: {cmu_id}")
    return resolved


def _add_cmu_selector(command_parser: argparse.ArgumentParser, *, action: str) -> None:
    selector = command_parser.add_mutually_exclusive_group(required=True)
    selector.add_argument(
        "--keyset-id",
        default=None,
        help=f"Treasurer CMU keyset id to {action}.",
    )
    selector.add_argument(
        "--cmu-id",
        default=None,
        help=f"Canonical CMU id, for example cmu-..., to {action}.",
    )


def cmu_create(args) -> int:
    nsec = _treasurer_nsec(args)
    mint = args.mint.rstrip("/")
    envelope = build_cmu_create_envelope(
        mint=mint,
        grant_id=args.grant_id,
        name=args.name,
        unit_alias=args.unit_alias,
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
    mint = args.mint.rstrip("/")
    keyset_id = _resolve_keyset_id(mint, args)
    issued = issue_treasury_units(
        mint,
        nsec,
        args.amount,
        keyset_id=keyset_id,
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


def _cmu_info(
    mint: str,
    nsec: str,
    lifetime_seconds: int,
    *,
    keyset_id: str,
) -> dict:
    envelope = build_cmu_info_envelope(
        mint=mint,
        nsec=nsec,
        keyset_id=keyset_id,
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
        return export_token(
            amount,
            wallet_path,
            mint=mint_url,
            unit=unit,
            memo=memo,
            remove=False,
        )
    except ValueError as exc:
        if str(exc) != "wallet cannot export exact amount with current proof set":
            raise

    selected = select_proofs_for_amount(
        amount,
        wallet_path,
        mint=mint_url,
        unit=unit,
    )
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
        mint=mint_url,
        unit=unit,
        change={
            "mint": swapped["mint"],
            "unit": unit,
            "quote": None,
            "amount": selected["amount"],
            "memo": memo,
            "proofs": replacement_proofs,
        },
    )
    return export_token(
        amount,
        wallet_path,
        mint=mint_url,
        unit=unit,
        memo=memo,
        remove=False,
    )


def send(args) -> int:
    nsec = _treasurer_nsec(args)
    mint = args.mint.rstrip("/")
    keyset_id = _resolve_keyset_id(mint, args)
    cmu = _cmu_info(mint, nsec, args.lifetime, keyset_id=keyset_id)
    if not mint_has_public_route(mint) and not args.allow_internal_mint_delivery:
        raise DeliveryError(
            "clear-treasury cannot deliver tokens from an internal-only mint; "
            "use a Safebox in the same Mainstay context, configure a public "
            "HTTPS mint URL, or explicitly allow internal delivery"
        )
    if not mint_has_public_route(mint) and not args.relay:
        raise DeliveryError(
            "internal mint delivery requires at least one explicit --relay"
        )
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
    withdrawn = export_token(
        args.amount,
        wallet_path,
        mint=mint,
        unit=cmu["unit"],
        memo=args.memo,
        remove=True,
    )
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
    keyset_id = _resolve_keyset_id(mint, args)
    envelope = build_cmu_info_envelope(
        mint=mint,
        nsec=nsec,
        keyset_id=keyset_id,
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


def cmu_summary(args) -> int:
    nsec = _treasurer_nsec(args)
    mint = args.mint.rstrip("/")
    keyset_id = _resolve_keyset_id(mint, args)
    envelope = build_cmu_summary_envelope(
        mint=mint,
        nsec=nsec,
        keyset_id=keyset_id,
        lifetime_seconds=args.lifetime,
    )
    result = request_json(mint, "POST", "/v1/treasury/cmus/summary", envelope)
    _print_json(
        {
            **result,
            "treasurer_npub": npub_from_nsec(nsec),
        }
    )
    return 0


def cmu_description(args) -> int:
    nsec = _treasurer_nsec(args)
    mint = args.mint.rstrip("/")
    keyset_id = _resolve_keyset_id(mint, args)
    envelope = build_cmu_description_envelope(
        mint=mint, nsec=nsec, keyset_id=keyset_id,
        description=read_description(args), lifetime_seconds=args.lifetime,
    )
    _print_json(request_json(mint, "POST", "/v1/treasury/cmus/description", envelope))
    return 0


def cmu_visibility(args) -> int:
    nsec = _treasurer_nsec(args)
    mint = args.mint.rstrip("/")
    keyset_id = _resolve_keyset_id(mint, args)
    envelope = build_cmu_visibility_envelope(
        mint=mint,
        nsec=nsec,
        keyset_id=keyset_id,
        public_listing=args.public_listing,
        lifetime_seconds=args.lifetime,
    )
    result = request_json(mint, "POST", "/v1/treasury/cmus/visibility", envelope)
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
    _add_cmu_selector(issue_parser, action="issue")
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
    _add_cmu_selector(send_parser, action="send")
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
        "--allow-internal-mint-delivery",
        action="store_true",
        help=(
            "Allow delivery from an internal-only mint when the operator knows "
            "the recipient shares that mint. Requires an explicit --relay."
        ),
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
        "--unit-alias",
        default=None,
        help="Friendly unit label, for example credits, passes, or meals.",
    )
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
    _add_cmu_selector(cmu_info_parser, action="inspect")
    cmu_info_parser.add_argument(
        "--lifetime",
        type=int,
        default=300,
        help="Signed request lifetime in seconds.",
    )
    cmu_info_parser.set_defaults(handler=cmu_info)
    cmu_summary_parser = cmu_subcommands.add_parser(
        "summary",
        help="Show supply totals for the CMU controlled by the treasurer nsec.",
    )
    _add_cmu_selector(cmu_summary_parser, action="summarize")
    cmu_summary_parser.add_argument(
        "--lifetime",
        type=int,
        default=300,
        help="Signed request lifetime in seconds.",
    )
    cmu_summary_parser.set_defaults(handler=cmu_summary)
    cmu_description_parser = cmu_subcommands.add_parser(
        "describe", help="Set or clear a description for your CMU.",
    )
    _add_cmu_selector(cmu_description_parser, action="describe")
    add_description_arguments(cmu_description_parser)
    cmu_description_parser.add_argument("--lifetime", type=int, default=300)
    cmu_description_parser.set_defaults(handler=cmu_description)
    cmu_private_parser = cmu_subcommands.add_parser(
        "private",
        help="Hide a treasurer-controlled CMU from the public homepage.",
    )
    _add_cmu_selector(cmu_private_parser, action="hide")
    cmu_private_parser.add_argument(
        "--lifetime",
        type=int,
        default=300,
        help="Signed request lifetime in seconds.",
    )
    cmu_private_parser.set_defaults(
        handler=cmu_visibility,
        public_listing=False,
    )
    cmu_publish_parser = cmu_subcommands.add_parser(
        "publish",
        help="Show a treasurer-controlled CMU on the public homepage.",
    )
    _add_cmu_selector(cmu_publish_parser, action="publish")
    cmu_publish_parser.add_argument(
        "--lifetime",
        type=int,
        default=300,
        help="Signed request lifetime in seconds.",
    )
    cmu_publish_parser.set_defaults(
        handler=cmu_visibility,
        public_listing=True,
    )

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
    except (DeliveryError, TreasuryAuthError, TreasuryError, ValueError) as exc:
        print(f"{program} {args.command} failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
