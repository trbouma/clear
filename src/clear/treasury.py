"""Prototype treasury client helpers for Clear Mint Notes."""

from __future__ import annotations

import json
import secrets
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from coincurve import PrivateKey, PublicKey

from clear.crypto import CURVE_ORDER, hash_to_curve
from clear.tokens import decode_token_v3, encode_token_v3


class TreasuryError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class BlindedOutput:
    amount: int
    secret: str
    r: int
    payload: dict[str, Any]


def split_amount(amount: int) -> list[int]:
    if amount <= 0:
        raise ValueError("amount must be greater than zero")
    denominations: list[int] = []
    bit = 1
    remaining = amount
    while remaining:
        if remaining & 1:
            denominations.append(bit)
        remaining >>= 1
        bit <<= 1
    return sorted(denominations, reverse=True)


def request_json(
    mint_url: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    *,
    token: str | None = None,
) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(
        f"{mint_url.rstrip('/')}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise TreasuryError(f"{method} {path} failed with {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise TreasuryError(f"{method} {path} failed: {exc.reason}") from exc


def blind_output(amount: int, keyset_id: str) -> BlindedOutput:
    secret = secrets.token_hex(32)
    r = secrets.randbelow(CURVE_ORDER - 1) + 1
    y = hash_to_curve(secret)
    r_key = PrivateKey(r.to_bytes(32, "big")).public_key
    blinded = PublicKey.combine_keys([y, r_key]).format(compressed=True).hex()
    return BlindedOutput(
        amount=amount,
        secret=secret,
        r=r,
        payload={"amount": amount, "id": keyset_id, "B_": blinded},
    )


def unblind_signature(
    output: BlindedOutput,
    promise: dict[str, Any],
    mint_public_key: str,
) -> dict[str, Any]:
    promise_point = PublicKey(bytes.fromhex(promise["C_"]))
    mint_key = PublicKey(bytes.fromhex(mint_public_key))
    negative_r = (CURVE_ORDER - output.r).to_bytes(32, "big")
    signature = PublicKey.combine_keys(
        [promise_point, mint_key.multiply(negative_r)]
    ).format(compressed=True)
    return {
        "amount": output.amount,
        "id": output.payload["id"],
        "secret": output.secret,
        "C": signature.hex(),
    }


def issue_token(
    mint_url: str,
    operator_token: str,
    amount: int,
    *,
    memo: str | None = None,
) -> dict[str, Any]:
    info = request_json(mint_url, "GET", "/v1/info")
    unit = info["currency"]["unit"]
    keyset = request_json(mint_url, "GET", "/v1/keys")["keysets"][0]
    keyset_id = keyset["id"]
    keys = keyset["keys"]

    denominations = split_amount(amount)
    missing = [
        denomination
        for denomination in denominations
        if str(denomination) not in keys
    ]
    if missing:
        raise TreasuryError(
            "mint does not advertise keys for denominations: "
            + ", ".join(str(each) for each in missing)
        )

    quote_payload: dict[str, Any] = {"amount": amount, "unit": unit}
    if memo:
        quote_payload["memo"] = memo
    quote = request_json(mint_url, "POST", "/v1/mint/quote/clear", quote_payload)
    request_json(
        mint_url,
        "POST",
        f"/v1/operator/quotes/{quote['quote']}/authorize",
        token=operator_token,
    )

    outputs = [blind_output(denomination, keyset_id) for denomination in denominations]
    minted = request_json(
        mint_url,
        "POST",
        "/v1/mint/clear",
        {"quote": quote["quote"], "outputs": [output.payload for output in outputs]},
    )

    promises = minted["signatures"]
    if len(promises) != len(outputs):
        raise TreasuryError("mint returned an unexpected number of signatures")

    proofs = [
        unblind_signature(output, promise, keys[str(output.amount)])
        for output, promise in zip(outputs, promises, strict=True)
    ]
    token = encode_token_v3(
        mint=mint_url,
        proofs=proofs,
        unit=unit,
        memo=memo,
    )
    return {
        "mint": mint_url.rstrip("/"),
        "unit": unit,
        "quote": quote["quote"],
        "amount": amount,
        "memo": memo,
        "token": token,
        "proofs": proofs,
    }


def swap_token_for_amount(
    mint_url: str,
    inputs: list[dict[str, Any]],
    amount: int,
    *,
    unit: str,
    memo: str | None = None,
) -> dict[str, Any]:
    if amount <= 0:
        raise TreasuryError("amount must be greater than zero")
    input_total = sum(int(proof["amount"]) for proof in inputs)
    if input_total < amount:
        raise TreasuryError("insufficient input amount for swap")

    keyset = request_json(mint_url, "GET", "/v1/keys")["keysets"][0]
    keyset_id = keyset["id"]
    keys = keyset["keys"]
    if any(proof.get("id") != keyset_id for proof in inputs):
        raise TreasuryError("wallet proofs are not for the mint's active keyset")

    send_outputs = [
        blind_output(denomination, keyset_id)
        for denomination in split_amount(amount)
    ]
    change_amount = input_total - amount
    change_outputs = [
        blind_output(denomination, keyset_id)
        for denomination in split_amount(change_amount)
    ] if change_amount else []
    outputs = [*send_outputs, *change_outputs]
    missing = [
        output.amount
        for output in outputs
        if str(output.amount) not in keys
    ]
    if missing:
        raise TreasuryError(
            "mint does not advertise keys for denominations: "
            + ", ".join(str(each) for each in sorted(set(missing)))
        )

    swapped = request_json(
        mint_url,
        "POST",
        "/v1/swap",
        {"inputs": inputs, "outputs": [output.payload for output in outputs]},
    )
    promises = swapped["signatures"]
    if len(promises) != len(outputs):
        raise TreasuryError("mint returned an unexpected number of swap signatures")
    proofs = [
        unblind_signature(output, promise, keys[str(output.amount)])
        for output, promise in zip(outputs, promises, strict=True)
    ]
    send_proofs = proofs[: len(send_outputs)]
    change_proofs = proofs[len(send_outputs) :]
    return {
        "mint": mint_url.rstrip("/"),
        "unit": unit,
        "amount": amount,
        "input_amount": input_total,
        "change_amount": change_amount,
        "token": encode_token_v3(
            mint=mint_url,
            proofs=send_proofs,
            unit=unit,
            memo=memo,
        ),
        "proofs": send_proofs,
        "change_proofs": change_proofs,
    }


def proofs_from_token(token: str) -> tuple[str, str | None, list[dict[str, Any]]]:
    payload = decode_token_v3(token.strip())
    token_entries = payload.get("token")
    if not isinstance(token_entries, list) or len(token_entries) != 1:
        raise TreasuryError("expected a token with exactly one mint entry")

    entry = token_entries[0]
    if not isinstance(entry, dict):
        raise TreasuryError("token mint entry must be an object")
    mint = entry.get("mint")
    proofs = entry.get("proofs")
    unit = payload.get("unit")
    if not isinstance(mint, str) or not mint:
        raise TreasuryError("token mint entry must include a mint URL")
    if not isinstance(proofs, list) or not proofs:
        raise TreasuryError("token must include at least one proof")
    for proof in proofs:
        if not isinstance(proof, dict):
            raise TreasuryError("token proofs must be objects")
    if unit is not None and not isinstance(unit, str):
        raise TreasuryError("token unit must be a string when present")
    return mint.rstrip("/"), unit, proofs


def redeem_token(
    mint_url: str,
    operator_token: str,
    token: str,
    *,
    memo: str | None = None,
) -> dict[str, Any]:
    token_mint, token_unit, proofs = proofs_from_token(token)
    configured_mint = mint_url.rstrip("/")
    if token_mint != configured_mint:
        raise TreasuryError(
            f"token is for mint {token_mint}, not configured mint {configured_mint}"
        )

    payload: dict[str, Any] = {"inputs": proofs}
    if memo:
        payload["memo"] = memo
    retired = request_json(
        configured_mint,
        "POST",
        "/v1/operator/retire",
        payload,
        token=operator_token,
    )
    return {
        "mint": configured_mint,
        "unit": retired.get("unit", token_unit),
        "amount": retired["amount"],
        "status": retired["status"],
        "memo": memo,
    }
