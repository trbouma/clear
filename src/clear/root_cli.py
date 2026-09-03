"""Privileged root bootstrap CLI for a Clear mint."""

from __future__ import annotations

import argparse
import json
import os
import sys
from ipaddress import ip_address
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv
from stroma import Keys

from clear.root_delivery import (
    DeliveryError,
    deliver_clear_token,
    discover_clear_support,
)
from clear.root_wallet import (
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
    issue_units,
    request_json,
    retire_proofs,
    retire_token,
    swap_token_for_amount,
)

DEFAULT_MINT_URL = "http://127.0.0.1:3339"
CONFIG_KEYS = {
    "currency_name": "CLEAR_CURRENCY_NAME",
    "currency_alias": "CLEAR_CURRENCY_ALIAS",
    "currency_unit_alias": "CLEAR_CURRENCY_UNIT_ALIAS",
    "root_authority_npub": "CLEAR_ROOT_AUTHORITY_NPUB",
    "mint_url": "CLEAR_MINT_URL",
}


def _is_loopback_url(url: str) -> bool:
    hostname = urlsplit(url).hostname
    if hostname is None:
        return False
    if hostname.rstrip(".").lower() == "localhost":
        return True
    try:
        return ip_address(hostname).is_loopback
    except ValueError:
        return False


def _api_url(args) -> str:
    url = (
        args.api_url or os.getenv("CLEAR_ROOT_API_URL") or DEFAULT_MINT_URL
    ).rstrip("/")
    if not _is_loopback_url(url):
        raise TreasuryError(
            "clear-root requires a loopback API URL; run it inside the mint "
            "container or trusted local mint environment"
        )
    return url


def _mint_info(api_url: str) -> dict:
    return request_json(api_url, "GET", "/v1/info")


def _public_mint_url(info: dict, api_url: str) -> str:
    configured = info.get("mint_url")
    if isinstance(configured, str) and configured.strip():
        return configured.rstrip("/")
    return api_url.rstrip("/")


def _operator_token() -> str:
    token = os.getenv("CLEAR_OPERATOR_TOKEN")
    if not token:
        raise TreasuryError("CLEAR_OPERATOR_TOKEN must be set")
    return token


def _sender_secret(args) -> str | None:
    return args.nsec or os.getenv("CLEAR_ROOT_NSEC") or None


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, indent=2))


def _wallet_path(args) -> Path:
    path = Path(args.wallet or os.getenv("CLEAR_ROOT_WALLET") or DEFAULT_WALLET_PATH)
    legacy = path.with_name("clear-lab-wallet.json")
    if path.name == DEFAULT_WALLET_PATH.name and not path.exists() and legacy.exists():
        try:
            legacy.replace(path)
        except OSError as exc:
            raise TreasuryError(f"unable to migrate root wallet: {exc}") from exc
    return path


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


def config(args) -> int:
    updates = {
        env_name: value
        for arg_name, env_name in CONFIG_KEYS.items()
        if (value := getattr(args, arg_name)) is not None
    }
    if not updates:
        raise TreasuryError("at least one configuration value must be supplied")
    env_file = Path(args.env_file)
    _update_env_file(env_file, updates)
    _print_json({"env_file": str(env_file), "updated": updates})
    return 0


def issue(args) -> int:
    issued = issue_units(
        _api_url(args),
        _operator_token(),
        args.amount,
        memo=args.memo,
    )
    if not args.to_token:
        summary = deposit_issue(issued, _wallet_path(args))
        issued = {
            key: value
            for key, value in issued.items()
            if key not in {"token", "proofs"}
        }
        issued["wallet"] = summary
    _print_json(issued)
    return 0


def _decode_proof_input(raw: str) -> tuple[list[dict], str | None]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TreasuryError(
            "retirement input must be a CMU amount, Cashu token, or proof JSON"
        ) from exc
    if isinstance(payload, list):
        proofs = payload
        unit = None
    elif isinstance(payload, dict):
        proofs = payload.get("proofs")
        unit = payload.get("unit")
    else:
        raise TreasuryError("proof JSON must be a list or an object containing proofs")
    if not isinstance(proofs, list) or not proofs:
        raise TreasuryError("proof JSON must contain at least one proof")
    if unit is not None and not isinstance(unit, str):
        raise TreasuryError("proof JSON unit must be a string")
    return proofs, unit


def retire(args) -> int:
    if args.proofs_file and args.value:
        raise TreasuryError("use either a retirement value or --proofs-file, not both")

    if args.value and args.value.isdecimal():
        amount = int(args.value)
        wallet_path = _wallet_path(args)
        pending = _export_or_swap(
            amount,
            wallet_path,
            api_url=_api_url(args),
            memo=args.memo,
        )
        retired = retire_token(
            _api_url(args),
            _operator_token(),
            pending["token"],
            memo=args.memo,
        )
        export_token(amount, wallet_path, memo=args.memo, remove=True)
        retired["wallet"] = wallet_summary(load_wallet(wallet_path), wallet_path)
        _print_json(retired)
        return 0

    if args.proofs_file:
        try:
            raw = Path(args.proofs_file).read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise TreasuryError(f"unable to read proof file: {exc}") from exc
    else:
        raw = args.value or sys.stdin.read().strip()
    if not raw:
        raise TreasuryError(
            "CMU amount, Cashu token, or proof JSON must be supplied"
        )

    if raw.startswith("cashu"):
        retired = retire_token(
            _api_url(args),
            _operator_token(),
            raw,
            memo=args.memo,
        )
    else:
        proofs, unit = _decode_proof_input(raw)
        retired = retire_proofs(
            _api_url(args),
            _operator_token(),
            proofs,
            unit=unit,
            memo=args.memo,
        )
    _print_json(retired)
    return 0


def redeem(args) -> int:
    """Compatibility command for the former retirement name."""

    return retire(args)


def summary(args) -> int:
    result = request_json(
        _api_url(args),
        "GET",
        "/v1/operator/summary",
        token=_operator_token(),
    )
    _print_json(result)
    return 0


def treasurer_add(args) -> int:
    result = request_json(
        _api_url(args),
        "POST",
        "/v1/operator/treasurers",
        {"npub": args.npub},
        token=_operator_token(),
    )
    _print_json(result)
    return 0


def treasurer_list(args) -> int:
    result = request_json(
        _api_url(args),
        "GET",
        "/v1/operator/treasurers",
        token=_operator_token(),
    )
    _print_json(result)
    return 0


def treasurer_grant(args) -> int:
    result = request_json(
        _api_url(args),
        "POST",
        "/v1/operator/treasurer-grants",
        {"npub": args.npub},
        token=_operator_token(),
    )
    _print_json(result)
    return 0


def treasurer_grant_list(args) -> int:
    result = request_json(
        _api_url(args),
        "GET",
        "/v1/operator/treasurer-grants",
        token=_operator_token(),
    )
    _print_json(result)
    return 0


def treasurer_keygen(args) -> int:
    keys = Keys()
    _print_json(
        {
            "npub": keys.public_key_bech32(),
            "nsec": keys.private_key_bech32(),
            "public_key": keys.public_key_hex(),
            "private_key": keys.private_key_hex(),
            "warning": (
                "Give the npub to the mint operator. Keep the nsec with the "
                "treasurer; the mint must never store it."
            ),
        }
    )
    return 0


def cmu_create(args) -> int:
    payload = {"grant_id": args.grant_id}
    if args.name:
        payload["name"] = args.name
    if args.unit_alias:
        payload["unit_alias"] = args.unit_alias
    result = request_json(
        _api_url(args),
        "POST",
        "/v1/operator/cmus",
        payload,
        token=_operator_token(),
    )
    _print_json(result)
    return 0


def cmu_list(args) -> int:
    result = request_json(
        _api_url(args),
        "GET",
        "/v1/operator/cmus",
        token=_operator_token(),
    )
    _print_json(result)
    return 0


def cmu_label(args) -> int:
    payload = {}
    if args.name:
        payload["name"] = args.name
    if args.unit_alias:
        payload["unit_alias"] = args.unit_alias
    result = request_json(
        _api_url(args),
        "POST",
        f"/v1/operator/cmus/{args.cmu}/label",
        payload,
        token=_operator_token(),
    )
    _print_json(result)
    return 0


def info(args) -> int:
    api_url = _api_url(args)
    mint_info = _mint_info(api_url)
    mint_url = _public_mint_url(mint_info, api_url)
    supply = request_json(
        api_url,
        "GET",
        "/v1/operator/summary",
        token=_operator_token(),
    )
    result = {
        "mint": mint_url,
        "api_url": api_url,
        "name": mint_info["name"],
        "version": mint_info["version"],
        "description": mint_info["description"],
        "currency": mint_info["currency"],
        "policy": mint_info.get("policy"),
        "circulation": {
            "issued": supply["issued"],
            "retired": supply["retired"],
            "circulating": supply.get("circulating", supply["outstanding"]),
            "outstanding": supply["outstanding"],
        },
    }
    _print_json(result)
    return 0


def address(args) -> int:
    api_url = _api_url(args)
    mint_info = _mint_info(api_url)
    mint_url = _public_mint_url(mint_info, api_url)
    currency = mint_info["currency"]
    _print_json(
        discover_clear_support(
            args.address,
            mint_url=mint_url,
            unit=currency["unit"],
        )
    )
    return 0


def send(args) -> int:
    api_url = _api_url(args)
    mint_info = _mint_info(api_url)
    mint_url = _public_mint_url(mint_info, api_url)
    currency = mint_info["currency"]
    discovery = discover_clear_support(
        args.address,
        mint_url=mint_url,
        unit=currency["unit"],
    )
    if not discovery["supported"]:
        raise DeliveryError("recipient does not advertise compatible Clear support")
    wallet_path = _wallet_path(args)
    pending = _export_or_swap(
        args.amount,
        wallet_path,
        api_url=api_url,
        memo=args.memo,
    )
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


def _export_or_swap(
    amount: int,
    wallet_path: Path,
    *,
    api_url: str,
    memo: str | None = None,
) -> dict:
    try:
        return export_token(amount, wallet_path, memo=memo, remove=False)
    except ValueError as exc:
        if str(exc) != "wallet cannot export exact amount with current proof set":
            raise

    selected = select_proofs_for_amount(amount, wallet_path)
    swapped = swap_token_for_amount(
        api_url,
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
            "mint": swapped["mint"],
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
    _export_or_swap(
        args.amount,
        wallet_path,
        api_url=_api_url(args),
        memo=args.memo,
    )
    withdrawn = export_token(args.amount, wallet_path, memo=args.memo, remove=True)
    _print_json(withdrawn)
    return 0


def parser(*, prog: str = "clear-root") -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog=prog,
        description=(
            "Privileged Clear root bootstrap CLI. This command requires "
            "operator access from .env and is not the production treasurer CLI."
        ),
    )
    result.add_argument(
        "--api-url",
        "--mint-url",
        dest="api_url",
        default=None,
        help=(
            "URL used to contact the Clear mint. clear-root requires loopback "
            f"and defaults to CLEAR_ROOT_API_URL, then {DEFAULT_MINT_URL}. "
            "--mint-url is an alternate spelling for --api-url."
        ),
    )
    result.add_argument(
        "--wallet",
        default=None,
        help=(
            "Root wallet JSON path. Defaults to CLEAR_ROOT_WALLET or "
            f"{DEFAULT_WALLET_PATH}."
        ),
    )

    subcommands = result.add_subparsers(dest="command", required=True)

    config_parser = subcommands.add_parser(
        "config",
        help="Set root mint display and governance values in an env file.",
    )
    config_parser.add_argument("--env-file", default=".env")
    config_parser.add_argument("--currency-name")
    config_parser.add_argument("--currency-alias")
    config_parser.add_argument("--currency-unit-alias")
    config_parser.add_argument("--root-authority-npub")
    config_parser.add_argument("--mint-url")
    config_parser.set_defaults(handler=config)

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

    issue_parser = subcommands.add_parser(
        "issue",
        help="Issue test CMU into circulation.",
    )
    issue_parser.add_argument("amount", type=int, help="Amount of CMU to issue.")
    issue_parser.add_argument("--memo", default=None, help="Optional quote memo.")
    issue_parser.add_argument(
        "--to-token",
        action="store_true",
        help=(
            "Encode the issued CMU as a Cashu token immediately instead of "
            "storing its proofs in the root wallet."
        ),
    )
    issue_parser.set_defaults(handler=issue)

    retire_parser = subcommands.add_parser(
        "retire",
        help="Remove CMU proofs permanently from circulation.",
    )
    retire_parser.add_argument(
        "value",
        nargs="?",
        help=(
            "CMU amount from the root wallet or a cashuA token. Reads a token "
            "or proof JSON from stdin when omitted."
        ),
    )
    retire_parser.add_argument(
        "--proofs-file",
        default=None,
        help="Read a proof list or {unit, proofs} object from a JSON file.",
    )
    retire_parser.add_argument("--memo", default=None, help="Optional retirement memo.")
    retire_parser.set_defaults(handler=retire)

    redeem_parser = subcommands.add_parser(
        "redeem",
        help="Compatibility alias for retire.",
    )
    redeem_parser.add_argument(
        "value",
        nargs="?",
        help="cashuA token string. Reads from stdin when omitted.",
    )
    redeem_parser.add_argument("--proofs-file", default=None, help=argparse.SUPPRESS)
    redeem_parser.add_argument("--memo", default=None, help="Optional retirement memo.")
    redeem_parser.set_defaults(handler=redeem)

    withdraw_parser = subcommands.add_parser(
        "withdraw",
        help="Export an exact token amount from the local root wallet.",
    )
    withdraw_parser.add_argument("amount", type=int)
    withdraw_parser.add_argument("--memo", default=None)
    withdraw_parser.set_defaults(handler=withdraw)

    send_parser = subcommands.add_parser(
        "send",
        help="Withdraw and deliver a token to a compatible Clear address.",
    )
    send_parser.add_argument("amount", type=int)
    send_parser.add_argument("address")
    send_parser.add_argument("--memo", default=None)
    send_parser.add_argument(
        "--nsec",
        default=None,
        help=(
            "Sender nsec or private key. Defaults to CLEAR_ROOT_NSEC, then an "
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

    treasurer_parser = subcommands.add_parser(
        "treasurer",
        help="Manage first-release treasurer authority records.",
    )
    treasurer_subcommands = treasurer_parser.add_subparsers(
        dest="treasurer_command",
        required=True,
    )
    treasurer_add_parser = treasurer_subcommands.add_parser(
        "add",
        help="Record a treasurer npub without receiving its nsec.",
    )
    treasurer_add_parser.add_argument("npub")
    treasurer_add_parser.set_defaults(handler=treasurer_add)
    treasurer_list_parser = treasurer_subcommands.add_parser(
        "list",
        help="List treasurer authority records.",
    )
    treasurer_list_parser.set_defaults(handler=treasurer_list)
    treasurer_grant_parser = treasurer_subcommands.add_parser(
        "grant",
        help="Set up one keyset/CMU creation path for a treasurer.",
    )
    treasurer_grant_parser.add_argument("npub")
    treasurer_grant_parser.set_defaults(handler=treasurer_grant)
    treasurer_grants_parser = treasurer_subcommands.add_parser(
        "grants",
        help="List treasurer keyset/CMU creation grants.",
    )
    treasurer_grants_parser.set_defaults(handler=treasurer_grant_list)
    treasurer_keygen_parser = treasurer_subcommands.add_parser(
        "keygen",
        help="Generate a local treasurer npub/nsec pair without storing it.",
    )
    treasurer_keygen_parser.set_defaults(handler=treasurer_keygen)

    cmu_parser = subcommands.add_parser(
        "cmu",
        help="Manage CMU creation and lifecycle records.",
    )
    cmu_subcommands = cmu_parser.add_subparsers(
        dest="cmu_command",
        required=True,
    )
    cmu_create_parser = cmu_subcommands.add_parser(
        "create",
        help="Create one CMU from a pending treasurer grant.",
    )
    cmu_create_parser.add_argument("grant_id")
    cmu_create_parser.add_argument("--name", default=None, help="Friendly CMU name.")
    cmu_create_parser.add_argument(
        "--unit-alias",
        default=None,
        help="Friendly unit label, for example credits, passes, or meals.",
    )
    cmu_create_parser.set_defaults(handler=cmu_create)
    cmu_list_parser = cmu_subcommands.add_parser(
        "list",
        help="List CMU records.",
    )
    cmu_list_parser.set_defaults(handler=cmu_list)
    cmu_label_parser = cmu_subcommands.add_parser(
        "label",
        help="Update wallet-facing CMU display labels.",
    )
    cmu_label_parser.add_argument("cmu", help="CMU unit or keyset ID.")
    cmu_label_parser.add_argument("--name", default=None, help="Friendly CMU name.")
    cmu_label_parser.add_argument(
        "--unit-alias",
        default=None,
        help="Friendly unit label, for example credits, passes, or meals.",
    )
    cmu_label_parser.set_defaults(handler=cmu_label)

    wallet_parser = subcommands.add_parser("wallet", help="Manage local root wallet.")
    wallet_subcommands = wallet_parser.add_subparsers(
        dest="wallet_command",
        required=True,
    )
    balance_parser = wallet_subcommands.add_parser(
        "balance",
        help="Show local root wallet balances.",
    )
    balance_parser.set_defaults(handler=wallet_balance)
    list_parser = wallet_subcommands.add_parser(
        "list",
        help="List local root wallet entries.",
    )
    list_parser.set_defaults(handler=wallet_list)
    export_parser = wallet_subcommands.add_parser(
        "export",
        help="Export an exact token amount from the local root wallet.",
    )
    export_parser.add_argument("amount", type=int)
    export_parser.add_argument("--memo", default=None)
    export_parser.set_defaults(handler=withdraw)

    return result


def main() -> int:
    load_dotenv(override=False)
    program = Path(sys.argv[0]).name or "clear-root"
    args = parser(prog=program).parse_args()
    try:
        return args.handler(args)
    except (DeliveryError, TreasuryError, ValueError) as exc:
        print(f"{program} {args.command} failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
