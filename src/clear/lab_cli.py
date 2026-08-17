"""Privileged lab CLI for exercising a local Clear mint."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from clear.lab_delivery import (
    DeliveryError,
    deliver_clear_token,
    discover_clear_support,
)
from clear.lab_wallet import (
    DEFAULT_WALLET_PATH,
    deposit_issue,
    export_token,
    load_wallet,
    replace_selected_with_change,
    select_proofs_for_amount,
    wallet_summary,
)
from clear.treasury import (
    TreasuryError,
    issue_token,
    redeem_token,
    request_json,
    swap_token_for_amount,
)

DEFAULT_MINT_URL = "http://127.0.0.1:3338"
CONFIGURE_KEYS = {
    "currency_name": "CLEAR_CURRENCY_NAME",
    "currency_alias": "CLEAR_CURRENCY_ALIAS",
    "currency_unit_alias": "CLEAR_CURRENCY_UNIT_ALIAS",
    "root_authority_npub": "CLEAR_ROOT_AUTHORITY_NPUB",
    "mint_url": "CLEAR_MINT_URL",
}


def _mint_url(args) -> str:
    return (args.mint_url or os.getenv("CLEAR_MINT_URL") or DEFAULT_MINT_URL).rstrip(
        "/"
    )


def _operator_token() -> str:
    token = os.getenv("CLEAR_OPERATOR_TOKEN")
    if not token:
        raise TreasuryError("CLEAR_OPERATOR_TOKEN must be set")
    return token


def _sender_secret(args) -> str | None:
    return args.nsec or os.getenv("CLEAR_LAB_NSEC")


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, indent=2))


def _wallet_path(args) -> Path:
    return Path(args.wallet or os.getenv("CLEAR_LAB_WALLET") or DEFAULT_WALLET_PATH)


def _quote_env_value(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _update_env_file(path: Path, updates: dict[str, str]) -> None:
    existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    seen: set[str] = set()
    output: list[str] = []
    for line in existing:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            output.append(line)
            continue
        name, _ = line.split("=", 1)
        key = name.strip()
        if key in updates:
            output.append(f"{key}={_quote_env_value(updates[key])}")
            seen.add(key)
        else:
            output.append(line)
    for key, value in updates.items():
        if key not in seen:
            output.append(f"{key}={_quote_env_value(value)}")
    path.write_text("\n".join(output) + "\n", encoding="utf-8")


def configure(args) -> int:
    updates = {
        env_name: value
        for arg_name, env_name in CONFIGURE_KEYS.items()
        if (value := getattr(args, arg_name)) is not None
    }
    if not updates:
        raise TreasuryError("at least one configuration value must be supplied")
    env_file = Path(args.env_file)
    _update_env_file(env_file, updates)
    _print_json({"env_file": str(env_file), "updated": updates})
    return 0


def issue(args) -> int:
    issued = issue_token(
        _mint_url(args),
        _operator_token(),
        args.amount,
        memo=args.memo,
    )
    if not args.to_token:
        summary = deposit_issue(issued, _wallet_path(args))
        issued = {**issued, "wallet": summary}
    _print_json(issued)
    return 0


def redeem(args) -> int:
    token = args.token or sys.stdin.read().strip()
    if not token:
        raise TreasuryError("token must be supplied as an argument or on stdin")
    redeemed = redeem_token(
        _mint_url(args),
        _operator_token(),
        token,
        memo=args.memo,
    )
    _print_json(redeemed)
    return 0


def summary(args) -> int:
    result = request_json(
        _mint_url(args),
        "GET",
        "/v1/operator/summary",
        token=_operator_token(),
    )
    _print_json(result)
    return 0


def info(args) -> int:
    mint_url = _mint_url(args)
    mint_info = request_json(mint_url, "GET", "/v1/info")
    supply = request_json(
        mint_url,
        "GET",
        "/v1/operator/summary",
        token=_operator_token(),
    )
    result = {
        "mint": mint_url,
        "name": mint_info["name"],
        "version": mint_info["version"],
        "description": mint_info["description"],
        "currency": mint_info["currency"],
        "policy": mint_info.get("policy"),
        "circulation": {
            "issued": supply["issued"],
            "retired": supply["retired"],
            "outstanding": supply["outstanding"],
        },
    }
    _print_json(result)
    return 0


def _mint_currency(mint_url: str) -> dict:
    return request_json(mint_url, "GET", "/v1/info")["currency"]


def address(args) -> int:
    mint_url = _mint_url(args)
    currency = _mint_currency(mint_url)
    _print_json(
        discover_clear_support(
            args.address,
            mint_url=mint_url,
            unit=currency["unit"],
        )
    )
    return 0


def send(args) -> int:
    mint_url = _mint_url(args)
    currency = _mint_currency(mint_url)
    discovery = discover_clear_support(
        args.address,
        mint_url=mint_url,
        unit=currency["unit"],
    )
    if not discovery["supported"]:
        raise DeliveryError("recipient does not advertise compatible Clear support")
    wallet_path = _wallet_path(args)
    pending = _export_or_swap(args.amount, wallet_path, memo=args.memo)
    delivery = deliver_clear_token(
        discovery,
        token=pending["token"],
        amount=args.amount,
        sender_secret=_sender_secret(args),
        memo=args.memo,
        relays=args.relay,
        expiration=args.expiration,
    )
    withdrawn = export_token(args.amount, wallet_path, memo=args.memo, remove=True)
    _print_json({**withdrawn, **delivery})
    return 0


def _export_or_swap(amount: int, wallet_path: Path, *, memo: str | None = None) -> dict:
    try:
        return export_token(amount, wallet_path, memo=memo, remove=False)
    except ValueError as exc:
        if str(exc) != "wallet cannot export exact amount with current proof set":
            raise

    selected = select_proofs_for_amount(amount, wallet_path)
    swapped = swap_token_for_amount(
        selected["mint"],
        selected["proofs"],
        amount,
        unit=selected["unit"],
        memo=memo,
    )
    replacement_proofs = [*swapped["proofs"], *swapped["change_proofs"]]
    replace_selected_with_change(
        selected["amount"],
        wallet_path,
        change={
            "mint": selected["mint"],
            "unit": selected["unit"],
            "quote": None,
            "amount": selected["amount"],
            "memo": memo,
            "proofs": replacement_proofs,
        },
    )
    return export_token(amount, wallet_path, memo=memo, remove=False)


def wallet_balance(args) -> int:
    path = _wallet_path(args)
    _print_json(wallet_summary(load_wallet(path), path))
    return 0


def wallet_list(args) -> int:
    path = _wallet_path(args)
    wallet = load_wallet(path)
    _print_json({"wallet": str(path), "entries": wallet["entries"]})
    return 0


def withdraw(args) -> int:
    wallet_path = _wallet_path(args)
    _export_or_swap(args.amount, wallet_path, memo=args.memo)
    withdrawn = export_token(args.amount, wallet_path, memo=args.memo, remove=True)
    _print_json(withdrawn)
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="clear-lab",
        description=(
            "Privileged Clear lab CLI for test mints. This command requires "
            "operator access from .env and is not the production treasurer CLI."
        ),
    )
    result.add_argument(
        "--mint-url",
        default=None,
        help=f"Clear mint URL. Defaults to CLEAR_MINT_URL or {DEFAULT_MINT_URL}.",
    )
    result.add_argument(
        "--wallet",
        default=None,
        help=(
            "Lab wallet JSON path. Defaults to CLEAR_LAB_WALLET or "
            f"{DEFAULT_WALLET_PATH}."
        ),
    )

    subcommands = result.add_subparsers(dest="command", required=True)

    configure_parser = subcommands.add_parser(
        "configure",
        help="Set lab mint display and governance values in an env file.",
    )
    configure_parser.add_argument("--env-file", default=".env")
    configure_parser.add_argument("--currency-name")
    configure_parser.add_argument("--currency-alias")
    configure_parser.add_argument("--currency-unit-alias")
    configure_parser.add_argument("--root-authority-npub")
    configure_parser.add_argument("--mint-url")
    configure_parser.set_defaults(handler=configure)

    info_parser = subcommands.add_parser(
        "info",
        help="Show CMU identity, policy metadata, and circulation totals.",
    )
    info_parser.set_defaults(handler=info)

    address_parser = subcommands.add_parser(
        "address",
        help="Check whether an address advertises support for this Clear CMU.",
    )
    address_parser.add_argument("address")
    address_parser.set_defaults(handler=address)

    issue_parser = subcommands.add_parser("issue", help="Issue a test Cashu token.")
    issue_parser.add_argument("amount", type=int, help="Amount of CMU to issue.")
    issue_parser.add_argument("--memo", default=None, help="Optional quote memo.")
    issue_parser.add_argument(
        "--to-token",
        action="store_true",
        help="Print the issued token immediately instead of storing it in the wallet.",
    )
    issue_parser.set_defaults(handler=issue)

    redeem_parser = subcommands.add_parser("redeem", help="Redeem a test Cashu token.")
    redeem_parser.add_argument(
        "token",
        nargs="?",
        help="cashuA token string. Reads from stdin when omitted.",
    )
    redeem_parser.add_argument("--memo", default=None, help="Optional redemption memo.")
    redeem_parser.set_defaults(handler=redeem)

    withdraw_parser = subcommands.add_parser(
        "withdraw",
        help="Export an exact token amount from the local lab wallet.",
    )
    withdraw_parser.add_argument("amount", type=int)
    withdraw_parser.add_argument("--memo", default=None)
    withdraw_parser.set_defaults(handler=withdraw)

    send_parser = subcommands.add_parser(
        "send",
        help="Withdraw and deliver a token to a compatible lab address.",
    )
    send_parser.add_argument("amount", type=int)
    send_parser.add_argument("address")
    send_parser.add_argument("--memo", default=None)
    send_parser.add_argument(
        "--nsec",
        default=None,
        help=(
            "Sender nsec or private key. Defaults to CLEAR_LAB_NSEC, then an "
            "ephemeral sender key."
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
    send_parser.set_defaults(handler=send)

    summary_parser = subcommands.add_parser("summary", help="Show mint supply totals.")
    summary_parser.set_defaults(handler=summary)

    wallet_parser = subcommands.add_parser("wallet", help="Manage local lab wallet.")
    wallet_subcommands = wallet_parser.add_subparsers(
        dest="wallet_command",
        required=True,
    )
    balance_parser = wallet_subcommands.add_parser(
        "balance",
        help="Show local lab wallet balances.",
    )
    balance_parser.set_defaults(handler=wallet_balance)
    list_parser = wallet_subcommands.add_parser(
        "list",
        help="List local lab wallet entries.",
    )
    list_parser.set_defaults(handler=wallet_list)
    export_parser = wallet_subcommands.add_parser(
        "export",
        help="Export an exact token amount from the local lab wallet.",
    )
    export_parser.add_argument("amount", type=int)
    export_parser.add_argument("--memo", default=None)
    export_parser.set_defaults(handler=withdraw)

    return result


def main() -> int:
    load_dotenv(override=False)
    args = parser().parse_args()
    try:
        return args.handler(args)
    except (DeliveryError, TreasuryError, ValueError) as exc:
        print(f"clear-lab {args.command} failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
