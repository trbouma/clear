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


def _compatible_proofs(
    wallet: dict[str, Any],
) -> tuple[str | None, str | None, list[tuple[int, int, dict[str, Any]]]]:
    selected_mint: str | None = None
    selected_unit: str | None = None
    proofs: list[tuple[int, int, dict[str, Any]]] = []
    for entry_index, entry in enumerate(wallet["entries"]):
        mint = entry["mint"]
        unit = entry["unit"]
        if selected_mint is None:
            selected_mint = mint
            selected_unit = unit
        if mint != selected_mint or unit != selected_unit:
            continue
        for proof_index, proof in enumerate(entry["proofs"]):
            proofs.append((entry_index, proof_index, proof))
    return selected_mint, selected_unit, proofs


def _best_selection(
    proofs: list[tuple[int, int, dict[str, Any]]],
    amount: int,
    *,
    exact: bool,
) -> list[tuple[int, int, dict[str, Any]]] | None:
    reachable: dict[int, list[tuple[int, int, dict[str, Any]]]] = {0: []}
    for candidate in proofs:
        proof_amount = int(candidate[2]["amount"])
        for total, selected in list(reachable.items()):
            next_total = total + proof_amount
            if next_total not in reachable:
                reachable[next_total] = [*selected, candidate]
    if exact:
        return reachable.get(amount)
    viable_totals = sorted(total for total in reachable if total >= amount)
    if not viable_totals:
        return None
    return reachable[viable_totals[0]]


def _remove_selected(
    wallet: dict[str, Any],
    selected: list[tuple[int, int, dict[str, Any]]],
) -> None:
    selected_positions = {
        (entry_index, proof_index) for entry_index, proof_index, _ in selected
    }
    for entry_index, entry in enumerate(wallet["entries"]):
        entry["proofs"] = [
            proof
            for proof_index, proof in enumerate(entry["proofs"])
            if (entry_index, proof_index) not in selected_positions
        ]
    wallet["entries"] = [entry for entry in wallet["entries"] if entry["proofs"]]


def select_proofs_for_amount(
    amount: int,
    path: Path = DEFAULT_WALLET_PATH,
) -> dict[str, Any]:
    wallet = load_wallet(path)
    selected_mint, selected_unit, proofs = _compatible_proofs(wallet)
    selected = _best_selection(proofs, amount, exact=False)
    if selected is None or selected_mint is None or selected_unit is None:
        raise ValueError("insufficient wallet balance")
    selected_total = sum(int(proof["amount"]) for _, _, proof in selected)
    return {
        "mint": selected_mint,
        "unit": selected_unit,
        "amount": selected_total,
        "proofs": [proof for _, _, proof in selected],
    }


def replace_selected_with_change(
    selected_amount: int,
    path: Path = DEFAULT_WALLET_PATH,
    *,
    change: dict[str, Any] | None = None,
) -> dict[str, Any]:
    wallet = load_wallet(path)
    _, _, proofs = _compatible_proofs(wallet)
    selected = _best_selection(proofs, selected_amount, exact=True)
    if selected is None:
        raise ValueError("selected wallet proofs changed before update")
    _remove_selected(wallet, selected)
    if change and change.get("proofs"):
        wallet["entries"].append(change)
    save_wallet(wallet, path)
    return wallet_summary(wallet, path)


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

    selected_mint, selected_unit, proofs = _compatible_proofs(wallet)
    selected = _best_selection(proofs, amount, exact=True)
    if selected is not None and selected_mint and selected_unit:
        selected_proofs = [proof for _, _, proof in selected]
        token = encode_token_v3(
            mint=selected_mint,
            proofs=selected_proofs,
            unit=selected_unit,
            memo=memo,
        )
        if remove:
            _remove_selected(wallet, selected)
            save_wallet(wallet, path)
        return {
            "mint": selected_mint,
            "unit": selected_unit,
            "amount": amount,
            "token": token,
            "proofs": selected_proofs,
        }
    if _best_selection(proofs, amount, exact=False) is not None:
        raise ValueError("wallet cannot export exact amount with current proof set")
    raise ValueError("insufficient wallet balance")
