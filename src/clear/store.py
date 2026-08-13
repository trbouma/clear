"""Atomic SQLite accounting for Clear issuance and proof retirement."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from clear.crypto import Keyset
from clear.models import BlindedMessage, Proof


class ClearError(ValueError):
    pass


class Store:
    def __init__(self, database_path: Path, keyset: Keyset):
        self.database_path = database_path
        self.keyset = keyset

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS mint_quotes (
                    id TEXT PRIMARY KEY,
                    keyset_id TEXT NOT NULL,
                    unit TEXT NOT NULL,
                    amount_requested INTEGER NOT NULL,
                    amount_paid INTEGER NOT NULL DEFAULT 0,
                    amount_issued INTEGER NOT NULL DEFAULT 0,
                    memo TEXT,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS issue_batches (
                    request_hash TEXT PRIMARY KEY,
                    quote_id TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    signatures TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS signed_outputs (
                    b_ TEXT PRIMARY KEY,
                    keyset_id TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    c_ TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS spent_proofs (
                    y TEXT PRIMARY KEY,
                    keyset_id TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    spent_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    keyset_id TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    reference TEXT,
                    created_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS mint_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )
            self._bind_mint_identity(connection)

    def _bind_mint_identity(self, connection) -> None:
        expected = {
            "keyset_id": self.keyset.id,
            "keyset_fingerprint": self.keyset.fingerprint,
            "protocol_unit": self.keyset.unit,
        }
        existing = {
            row["key"]: row["value"]
            for row in connection.execute("SELECT key, value FROM mint_metadata")
        }
        if not existing:
            prior_quote = connection.execute(
                "SELECT keyset_id, unit FROM mint_quotes LIMIT 1"
            ).fetchone()
            if prior_quote is not None and (
                prior_quote["keyset_id"] != self.keyset.id
                or prior_quote["unit"] != self.keyset.unit
            ):
                raise RuntimeError(
                    "existing Clear database belongs to a different keyset currency"
                )
            connection.executemany(
                "INSERT INTO mint_metadata(key, value) VALUES (?, ?)",
                expected.items(),
            )
            return
        if existing != expected:
            raise RuntimeError(
                "configured keyset does not match the currency bound to this database"
            )

    @contextmanager
    def _connection(self):
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    @contextmanager
    def _transaction(self):
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            yield connection

    @staticmethod
    def _now(previous: int | None = None) -> int:
        current = int(time.time())
        return max(current, (previous or 0) + 1)

    def create_quote(self, amount: int, unit: str, memo: str | None) -> dict:
        if unit != self.keyset.unit:
            raise ClearError("quote unit is not issued by this Clear mint")
        quote_id = str(uuid.uuid4())
        now = self._now()
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO mint_quotes VALUES (?, ?, ?, ?, 0, 0, ?, ?, ?)",
                (quote_id, self.keyset.id, unit, amount, memo, now, now),
            )
        return self.get_quote(quote_id)

    def authorize_quote(self, quote_id: str) -> dict:
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT * FROM mint_quotes WHERE id = ?", (quote_id,)
            ).fetchone()
            if row is None:
                raise ClearError("quote not found")
            updated_at = self._now(row["updated_at"])
            connection.execute(
                "UPDATE mint_quotes SET amount_paid = amount_requested, updated_at = ? "
                "WHERE id = ?",
                (updated_at, quote_id),
            )
            self._audit(connection, "authorize", row["amount_requested"], quote_id)
        return self.get_quote(quote_id)

    def get_quote(self, quote_id: str) -> dict:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM mint_quotes WHERE id = ?", (quote_id,)
            ).fetchone()
        if row is None:
            raise ClearError("quote not found")
        return {
            "quote": row["id"],
            "request": f"clear:{row['id']}",
            "unit": row["unit"],
            "method": "clear",
            "amount_paid": row["amount_paid"],
            "amount_issued": row["amount_issued"],
            "updated_at": row["updated_at"],
            "memo": row["memo"],
        }

    def issue(self, quote_id: str, outputs: list[BlindedMessage]) -> list[dict]:
        self._validate_outputs(outputs)
        canonical = json.dumps(
            [output.model_dump(by_alias=True) for output in outputs],
            sort_keys=True,
            separators=(",", ":"),
        )
        request_hash = hashlib.sha256(f"{quote_id}:{canonical}".encode()).hexdigest()
        with self._transaction() as connection:
            prior = connection.execute(
                "SELECT quote_id, signatures FROM issue_batches WHERE request_hash = ?",
                (request_hash,),
            ).fetchone()
            if prior is not None:
                if prior["quote_id"] != quote_id:
                    raise ClearError("issuance request collision")
                return json.loads(prior["signatures"])

            quote = connection.execute(
                "SELECT * FROM mint_quotes WHERE id = ?", (quote_id,)
            ).fetchone()
            if quote is None:
                raise ClearError("quote not found")
            amount = sum(output.amount for output in outputs)
            available = quote["amount_paid"] - quote["amount_issued"]
            if amount > available:
                raise ClearError("outputs exceed the authorized quote amount")
            signatures = self._sign_outputs(
                connection, outputs, operation=f"issue:{quote_id}"
            )
            updated_at = self._now(quote["updated_at"])
            connection.execute(
                "UPDATE mint_quotes SET amount_issued = amount_issued + ?, "
                "updated_at = ? WHERE id = ?",
                (amount, updated_at, quote_id),
            )
            connection.execute(
                "INSERT INTO issue_batches VALUES (?, ?, ?, ?)",
                (request_hash, quote_id, amount, json.dumps(signatures)),
            )
            self._audit(connection, "issue", amount, quote_id)
            return signatures

    def swap(self, inputs: list[Proof], outputs: list[BlindedMessage]) -> list[dict]:
        self._validate_outputs(outputs)
        verified = self._verify_inputs(inputs)
        input_amount = sum(proof.amount for proof, _ in verified)
        output_amount = sum(output.amount for output in outputs)
        if input_amount != output_amount:
            raise ClearError("input and output amounts must be equal")
        with self._transaction() as connection:
            self._ensure_unspent(connection, verified)
            self._spend(connection, verified, "swap")
            signatures = self._sign_outputs(connection, outputs, operation="swap")
            self._audit(connection, "swap", input_amount, None)
            return signatures

    def retire(self, inputs: list[Proof], memo: str | None) -> int:
        verified = self._verify_inputs(inputs)
        amount = sum(proof.amount for proof, _ in verified)
        with self._transaction() as connection:
            self._ensure_unspent(connection, verified)
            self._spend(connection, verified, "retire")
            self._audit(connection, "retire", amount, memo)
        return amount

    def states(self, ys: list[str]) -> list[dict]:
        placeholders = ",".join("?" for _ in ys)
        with self._connection() as connection:
            spent = {
                row["y"]
                for row in connection.execute(
                    f"SELECT y FROM spent_proofs WHERE y IN ({placeholders})",
                    ys,
                )
            }
        return [
            {"Y": y, "state": "SPENT" if y in spent else "UNSPENT", "witness": None}
            for y in ys
        ]

    def summary(self) -> dict:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT action, COALESCE(SUM(amount), 0) amount FROM audit_log "
                "GROUP BY action"
            ).fetchall()
        totals = {row["action"]: row["amount"] for row in rows}
        issued = totals.get("issue", 0)
        retired = totals.get("retire", 0)
        return {
            "unit": self.keyset.unit,
            "keyset_id": self.keyset.id,
            "issued": issued,
            "retired": retired,
            "outstanding": issued - retired,
        }

    def _validate_outputs(self, outputs: list[BlindedMessage]) -> None:
        if any(output.id != self.keyset.id for output in outputs):
            raise ClearError("outputs must use this Clear currency's active keyset")
        blinded = [output.blinded_secret for output in outputs]
        if len(blinded) != len(set(blinded)):
            raise ClearError("duplicate blinded outputs are not allowed")
        for output in outputs:
            if output.amount not in self.keyset.private_keys:
                raise ClearError(f"unsupported denomination: {output.amount}")

    def _sign_outputs(self, connection, outputs, operation: str) -> list[dict]:
        for output in outputs:
            if connection.execute(
                "SELECT 1 FROM signed_outputs WHERE b_ = ?",
                (output.blinded_secret,),
            ).fetchone():
                raise ClearError("blinded output has already been signed")
        now = self._now()
        signatures = []
        for output in outputs:
            signature = self.keyset.sign_blinded(output.amount, output.blinded_secret)
            connection.execute(
                "INSERT INTO signed_outputs VALUES (?, ?, ?, ?, ?, ?)",
                (
                    output.blinded_secret,
                    self.keyset.id,
                    output.amount,
                    signature,
                    operation,
                    now,
                ),
            )
            signatures.append(
                {"amount": output.amount, "id": self.keyset.id, "C_": signature}
            )
        return signatures

    def _verify_inputs(self, inputs: list[Proof]) -> list[tuple[Proof, str]]:
        if any(proof.id != self.keyset.id for proof in inputs):
            raise ClearError("proofs from another Clear currency cannot be combined")
        verified: list[tuple[Proof, str]] = []
        for proof in inputs:
            try:
                y = self.keyset.verify_proof(
                    proof.amount, proof.secret, proof.signature
                )
            except ValueError as exc:
                raise ClearError(str(exc)) from exc
            verified.append((proof, y))
        ys = [y for _, y in verified]
        if len(ys) != len(set(ys)):
            raise ClearError("duplicate proofs are not allowed")
        return verified

    @staticmethod
    def _ensure_unspent(connection, verified: list[tuple[Proof, str]]) -> None:
        for _, y in verified:
            if connection.execute(
                "SELECT 1 FROM spent_proofs WHERE y = ?", (y,)
            ).fetchone():
                raise ClearError("proof is already spent")

    def _spend(self, connection, verified, reason: str) -> None:
        now = self._now()
        connection.executemany(
            "INSERT INTO spent_proofs VALUES (?, ?, ?, ?, ?)",
            [(y, self.keyset.id, proof.amount, reason, now) for proof, y in verified],
        )

    def _audit(
        self, connection, action: str, amount: int, reference: str | None
    ) -> None:
        connection.execute(
            "INSERT INTO audit_log(action, keyset_id, amount, reference, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (action, self.keyset.id, amount, reference, self._now()),
        )
