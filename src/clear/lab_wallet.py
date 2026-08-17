"""Simple JSON wallet for Clear lab tokens."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from clear.tokens import encode_token_v3

DEFAULT_WALLET_PATH = Path("data/clear-lab-wallet.json")


def empty_wallet() -> dict[str, Any]:
    return {"version": 1, "entries": []}


def load_wallet(path: Path = DEFAULT_WALLET_PATH) -> dict[str, Any]:
    if not path.exists():
        return empty_wallet()
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("lab wallet must contain a JSON object")
    if loaded.get("version") != 1:
        raise ValueError("unsupported lab wallet version")
    if not isinstance(loaded.get("entries"), list):
        raise ValueError("lab wallet entries must be a list")
    return loaded


def save_wallet(wallet: dict[str, Any], path: Path = DEFAULT_WALLET_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(wallet, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def deposit_issue(
    issued: dict[str, Any],
    path: Path = DEFAULT_WALLET_PATH,
) -> dict[str, Any]:
    wallet = load_wallet(path)
    entry = {
        "mint": issued["mint"],
        "unit": issued["unit"],
        "quote": issued.get("quote"),
        "amount": issued["amount"],
        "memo": issued.get("memo"),
        "proofs": issued["proofs"],
    }
    wallet["entries"].append(entry)
    save_wallet(wallet, path)
    return wallet_summary(wallet, path)


def wallet_summary(
    wallet: dict[str, Any],
    path: Path = DEFAULT_WALLET_PATH,
) -> dict[str, Any]:
    balances: dict[tuple[str, str], int] = {}
    for entry in wallet["entries"]:
        key = (entry["mint"], entry["unit"])
        balances[key] = balances.get(key, 0) + sum(
            proof["amount"] for proof in entry["proofs"]
        )
    return {
        "wallet": str(path),
        "entries": len(wallet["entries"]),
        "balances": [
            {"mint": mint, "unit": unit, "amount": amount}
            for (mint, unit), amount in sorted(balances.items())
        ],
    }


def export_token(
    amount: int,
    path: Path = DEFAULT_WALLET_PATH,
    *,
    memo: str | None = None,
    remove: bool = True,
) -> dict[str, Any]:
    wallet = load_wallet(path)
    if amount <= 0:
        raise ValueError("amount must be greater than zero")

    selected: list[dict[str, Any]] = []
    selected_total = 0
    selected_mint: str | None = None
    selected_unit: str | None = None
    selected_ids: set[int] = set()
    for entry in wallet["entries"]:
        for proof in entry["proofs"]:
            mint = entry["mint"]
            unit = entry["unit"]
            if selected_mint is None:
                selected_mint = mint
                selected_unit = unit
            if mint != selected_mint or unit != selected_unit:
                continue
            selected.append(proof)
            selected_ids.add(id(proof))
            selected_total += proof["amount"]
            if selected_total == amount:
                token = encode_token_v3(
                    mint=selected_mint,
                    proofs=selected,
                    unit=selected_unit or "",
                    memo=memo,
                )
                if remove:
                    for wallet_entry in wallet["entries"]:
                        wallet_entry["proofs"] = [
                            wallet_proof
                            for wallet_proof in wallet_entry["proofs"]
                            if id(wallet_proof) not in selected_ids
                        ]
                    wallet["entries"] = [
                        wallet_entry
                        for wallet_entry in wallet["entries"]
                        if wallet_entry["proofs"]
                    ]
                    save_wallet(wallet, path)
                return {
                    "mint": selected_mint,
                    "unit": selected_unit,
                    "amount": amount,
                    "token": token,
                    "proofs": selected,
                }
            if selected_total > amount:
                raise ValueError(
                    "wallet cannot export exact amount with current proof set"
                )
    raise ValueError("insufficient wallet balance")
