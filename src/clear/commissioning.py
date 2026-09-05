"""Root-owned commissioning verification for a Clear mint."""

from __future__ import annotations

import hashlib
import json

from clear.config import Settings
from clear.crypto import Keyset, hash_to_curve
from clear.models import BlindedMessage, Proof
from clear.store import SCHEMA_VERSION, ClearError, Store
from clear.tokens import decode_token_v3, encode_token_v3
from clear.treasury import blind_output, unblind_signature

VERIFICATION_AMOUNT = 3


def configuration_fingerprint(
    settings: Settings,
    keyset: Keyset,
    *,
    software_version: str,
) -> str:
    encryption_material = settings.key_encryption_key or settings.master_secret
    payload = {
        "schema_version": SCHEMA_VERSION,
        "software_version": software_version,
        "mint_url": settings.mint_url.rstrip("/"),
        "root_keyset_id": keyset.id,
        "root_authority_npub": settings.root_authority_npub,
        "max_order": settings.max_order,
        "key_encryption_key_id": hashlib.sha256(
            f"clear-key-encryption-v1:{encryption_material}".encode()
        ).hexdigest(),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def _proof_y(proof: dict) -> str:
    return hash_to_curve(proof["secret"]).format(compressed=True).hex()


def _record(checks: list[dict], name: str, passed: bool, detail: str) -> None:
    checks.append({"name": name, "passed": passed, "detail": detail})
    if not passed:
        raise ClearError(f"commissioning check failed: {name}: {detail}")


def run_verification(store: Store, *, mint_url: str) -> dict:
    run = store.begin_commissioning_verification()
    verification_id = run["id"]
    keyset = store.keysets[run["keyset_id"]]
    checks: list[dict] = []
    try:
        _record(
            checks,
            "configuration",
            bool(store.configuration_fingerprint),
            "critical configuration has a stable fingerprint",
        )
        _record(
            checks,
            "encrypted-keyset-persistence",
            store.commissioning_keyset_persists(keyset.id),
            "commissioning keyset decrypts to its persisted identity",
        )
        keyset_response = store.keyset_response(keyset.id, include_keys=True)
        _record(
            checks,
            "key-discovery",
            keyset_response["id"] == keyset.id
            and keyset_response["unit"] == keyset.unit
            and keyset_response["active"] is False
            and bool(keyset_response["keys"]),
            "commissioning keys are discoverable and marked inactive",
        )

        quote = store.create_quote(
            VERIFICATION_AMOUNT,
            keyset.unit,
            "Clear root commissioning verification",
            allow_commissioning=True,
        )
        authorized = store.authorize_quote(quote["quote"])
        _record(
            checks,
            "quote-authorization",
            authorized["amount_paid"] == VERIFICATION_AMOUNT,
            "commissioning quote was authorized through the shared action layer",
        )

        issue_outputs = [blind_output(2, keyset.id), blind_output(1, keyset.id)]
        promises = store.issue(
            quote["quote"],
            [BlindedMessage.model_validate(output.payload) for output in issue_outputs],
        )
        proofs = [
            unblind_signature(
                output,
                promise,
                keyset.public_keys[output.amount],
            )
            for output, promise in zip(issue_outputs, promises, strict=True)
        ]
        issued_states = store.states([_proof_y(proof) for proof in proofs])
        _record(
            checks,
            "blinded-issuance",
            sum(proof["amount"] for proof in proofs) == VERIFICATION_AMOUNT
            and all(state["state"] == "UNSPENT" for state in issued_states),
            "issued proofs unblind and begin unspent",
        )

        token = encode_token_v3(
            mint=mint_url,
            proofs=proofs,
            unit=keyset.unit,
            memo="Clear root commissioning verification",
        )
        decoded = decode_token_v3(token)
        _record(
            checks,
            "token-round-trip",
            decoded["unit"] == keyset.unit
            and decoded["token"][0]["mint"] == mint_url.rstrip("/"),
            "commissioning proofs survive canonical token encoding",
        )

        swap_outputs = [blind_output(1, keyset.id), blind_output(2, keyset.id)]
        swap_promises = store.swap(
            [Proof.model_validate(proof) for proof in proofs],
            [BlindedMessage.model_validate(output.payload) for output in swap_outputs],
        )
        swapped_proofs = [
            unblind_signature(
                output,
                promise,
                keyset.public_keys[output.amount],
            )
            for output, promise in zip(swap_outputs, swap_promises, strict=True)
        ]
        old_states = store.states([_proof_y(proof) for proof in proofs])
        new_states = store.states([_proof_y(proof) for proof in swapped_proofs])
        _record(
            checks,
            "swap-and-proof-state",
            all(state["state"] == "SPENT" for state in old_states)
            and all(state["state"] == "UNSPENT" for state in new_states),
            "swap spends every input and creates unspent replacement proofs",
        )

        retired = store.retire(
            [Proof.model_validate(proof) for proof in swapped_proofs],
            "Clear root commissioning verification",
        )
        retired_states = store.states([_proof_y(proof) for proof in swapped_proofs])
        _record(
            checks,
            "retirement",
            retired["amount"] == VERIFICATION_AMOUNT
            and all(state["state"] == "SPENT" for state in retired_states),
            "all commissioning proofs were permanently retired",
        )

        summary = store.summary_for_keyset(keyset.id)
        _record(
            checks,
            "supply-reconciliation",
            summary["issued"] == VERIFICATION_AMOUNT
            and summary["retired"] == VERIFICATION_AMOUNT
            and summary["outstanding"] == 0,
            "commissioning supply reconciles to zero outstanding",
        )
        actions = store.audit_actions(keyset.id)
        required_actions = {
            "commissioning:start",
            "authorize",
            "issue",
            "swap",
            "retire",
        }
        _record(
            checks,
            "audit-trail",
            required_actions.issubset(actions),
            "all commissioning mutations have ordered audit records",
        )

        evidence = {
            "checks": checks,
            "digest": hashlib.sha256(
                json.dumps(checks, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
        }
        return store.complete_commissioning_verification(
            verification_id,
            evidence=evidence,
            expected_amount=VERIFICATION_AMOUNT,
        )
    except Exception as exc:
        store.fail_commissioning_verification(verification_id, str(exc))
        if isinstance(exc, ClearError):
            raise
        raise ClearError(f"commissioning verification failed: {exc}") from exc
