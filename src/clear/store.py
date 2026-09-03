"""Atomic SQLite accounting for Clear issuance and proof retirement."""

from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from clear.crypto import Keyset
from clear.models import BlindedMessage, Proof
from clear.treasury_auth import TreasuryAuthError, npub_to_hex, verify_envelope


class ClearError(ValueError):
    pass


SCHEMA_VERSION = 1


class Store:
    def __init__(
        self,
        database_path: Path,
        keyset: Keyset,
        *,
        key_encryption_key: str | None = None,
    ):
        self.database_path = database_path
        self.keyset = keyset
        self.key_encryption_key = key_encryption_key
        self.keysets: dict[str, Keyset] = {keyset.id: keyset}
        self.keyset_order: list[str] = [keyset.id]

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
                CREATE TABLE IF NOT EXISTS treasurers (
                    npub TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    added_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    removed_at INTEGER
                );
                CREATE TABLE IF NOT EXISTS treasurer_grants (
                    id TEXT PRIMARY KEY,
                    npub TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    max_uses INTEGER NOT NULL,
                    uses INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    consumed_at INTEGER,
                    keyset_id TEXT,
                    FOREIGN KEY(npub) REFERENCES treasurers(npub)
                );
                CREATE TABLE IF NOT EXISTS cmus (
                    keyset_id TEXT PRIMARY KEY,
                    unit TEXT NOT NULL UNIQUE,
                    fingerprint TEXT NOT NULL,
                    status TEXT NOT NULL,
                    friendly_name TEXT,
                    treasurer_npub TEXT,
                    material_kind TEXT NOT NULL,
                    encrypted_secret TEXT,
                    public_keys TEXT NOT NULL,
                    max_order INTEGER NOT NULL,
                    created_at INTEGER NOT NULL,
                    activated_at INTEGER,
                    FOREIGN KEY(treasurer_npub) REFERENCES treasurers(npub)
                );
                CREATE TABLE IF NOT EXISTS treasury_nonces (
                    nonce TEXT PRIMARY KEY,
                    pubkey TEXT NOT NULL,
                    action TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                );
                """
            )
            connection.execute(
                "INSERT OR IGNORE INTO mint_metadata(key, value) VALUES (?, ?)",
                ("schema_version", str(SCHEMA_VERSION)),
            )
            self._bind_mint_identity(connection)
            self._ensure_legacy_cmu(connection)
            self._load_persisted_keysets(connection)

    def _bind_mint_identity(self, connection) -> None:
        expected = {
            "keyset_id": self.keyset.id,
            "keyset_fingerprint": self.keyset.fingerprint,
            "protocol_unit": self.keyset.unit,
        }
        existing = {
            row["key"]: row["value"]
            for row in connection.execute(
                "SELECT key, value FROM mint_metadata "
                "WHERE key IN ('keyset_id', 'keyset_fingerprint', 'protocol_unit')"
            )
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

    @staticmethod
    def _normalize_npub(npub: str) -> str:
        normalized = npub.strip()
        if not normalized:
            raise ClearError("treasurer npub must not be empty")
        if normalized.lower().startswith("nsec"):
            raise ClearError("treasurer nsec must never be submitted to the mint")
        is_hex_pubkey = (
            len(normalized) == 64
            and all(c in "0123456789abcdefABCDEF" for c in normalized)
        )
        if not (
            normalized.lower().startswith("npub")
            or is_hex_pubkey
        ):
            raise ClearError("treasurer must be an npub or 32-byte hex public key")
        return normalized

    def _ensure_legacy_cmu(self, connection) -> None:
        now = self._now()
        connection.execute(
            """
            INSERT OR IGNORE INTO cmus(
                keyset_id, unit, fingerprint, status, friendly_name,
                treasurer_npub, material_kind, encrypted_secret, public_keys,
                max_order, created_at, activated_at
            )
            VALUES (
                ?, ?, ?, 'active', NULL, NULL, 'legacy-derived-v1', NULL, ?, ?, ?, ?
            )
            """,
            (
                self.keyset.id,
                self.keyset.unit,
                self.keyset.fingerprint,
                json.dumps(self.keyset.public_keys, sort_keys=True),
                len(self.keyset.public_keys) - 1,
                now,
                now,
            ),
        )

    def _load_persisted_keysets(self, connection) -> None:
        self.keysets = {self.keyset.id: self.keyset}
        self.keyset_order = [self.keyset.id]
        rows = connection.execute(
            "SELECT * FROM cmus WHERE keyset_id != ? ORDER BY created_at, keyset_id",
            (self.keyset.id,),
        ).fetchall()
        for row in rows:
            if row["material_kind"] != "random-encrypted-v1":
                raise RuntimeError(
                    f"unsupported keyset material: {row['material_kind']}"
                )
            if not row["encrypted_secret"]:
                raise RuntimeError(
                    f"missing encrypted secret for keyset {row['keyset_id']}"
                )
            secret = self._decrypt_keyset_secret(row["encrypted_secret"])
            keyset = Keyset(secret, max_order=row["max_order"])
            if (
                keyset.id != row["keyset_id"]
                or keyset.unit != row["unit"]
                or keyset.fingerprint != row["fingerprint"]
            ):
                raise RuntimeError(
                    f"persisted keyset identity mismatch: {row['keyset_id']}"
                )
            self.keysets[keyset.id] = keyset
            self.keyset_order.append(keyset.id)

    def _encryption_key(self) -> bytes:
        if not self.key_encryption_key:
            raise RuntimeError("key encryption key is required for random keysets")
        material = self.key_encryption_key
        return hashlib.sha256(f"clear-key-encryption-v1:{material}".encode()).digest()

    def _encrypt_keyset_secret(self, secret: str) -> str:
        nonce = secrets.token_bytes(12)
        ciphertext = AESGCM(self._encryption_key()).encrypt(
            nonce,
            secret.encode(),
            b"clear-random-keyset-secret-v1",
        )
        return json.dumps(
            {
                "format": "aes-256-gcm",
                "key_version": "clear-key-encryption-v1",
                "nonce": nonce.hex(),
                "ciphertext": ciphertext.hex(),
            },
            sort_keys=True,
        )

    def _decrypt_keyset_secret(self, payload: str) -> str:
        data = json.loads(payload)
        if data.get("format") != "aes-256-gcm":
            raise RuntimeError("unsupported encrypted keyset secret format")
        plaintext = AESGCM(self._encryption_key()).decrypt(
            bytes.fromhex(data["nonce"]),
            bytes.fromhex(data["ciphertext"]),
            b"clear-random-keyset-secret-v1",
        )
        return plaintext.decode()

    def _keyset_for_unit(self, unit: str) -> Keyset:
        for keyset in self.keysets.values():
            if keyset.unit == unit:
                return keyset
        raise ClearError("quote unit is not issued by this Clear mint")

    def _keyset_response(self, keyset: Keyset, *, include_keys: bool) -> dict:
        response = {
            "id": keyset.id,
            "unit": keyset.unit,
            "active": self._cmu_status(keyset.id) == "active",
            "input_fee_ppk": 0,
            "final_expiry": None,
        }
        if include_keys:
            response["keys"] = {
                str(amount): key for amount, key in keyset.public_keys.items()
            }
        return response

    def _cmu_status(self, keyset_id: str) -> str:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT status FROM cmus WHERE keyset_id = ?", (keyset_id,)
            ).fetchone()
        return row["status"] if row is not None else "active"

    def keyset_responses(self, *, include_keys: bool) -> list[dict]:
        return [
            self._keyset_response(self.keysets[keyset_id], include_keys=include_keys)
            for keyset_id in self.keyset_order
        ]

    def keyset_response(self, keyset_id: str, *, include_keys: bool) -> dict:
        keyset = self.keysets.get(keyset_id)
        if keyset is None:
            raise ClearError("keyset not found")
        return self._keyset_response(keyset, include_keys=include_keys)

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
        keyset = self._keyset_for_unit(unit)
        quote_id = str(uuid.uuid4())
        now = self._now()
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO mint_quotes VALUES (?, ?, ?, ?, 0, 0, ?, ?, ?)",
                (quote_id, keyset.id, unit, amount, memo, now, now),
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
            keyset = self.keysets.get(quote["keyset_id"])
            if keyset is None:
                raise ClearError("quote keyset is not available")
            self._validate_outputs(outputs, keyset)
            amount = sum(output.amount for output in outputs)
            available = quote["amount_paid"] - quote["amount_issued"]
            if amount > available:
                raise ClearError("outputs exceed the authorized quote amount")
            signatures = self._sign_outputs(
                connection,
                outputs,
                keyset,
                operation=f"issue:{quote_id}",
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
        input_keyset = self._single_input_keyset(inputs)
        self._validate_outputs(outputs, input_keyset)
        verified = self._verify_inputs(inputs, input_keyset)
        input_amount = sum(proof.amount for proof, _ in verified)
        output_amount = sum(output.amount for output in outputs)
        if input_amount != output_amount:
            raise ClearError("input and output amounts must be equal")
        with self._transaction() as connection:
            self._ensure_unspent(connection, verified)
            self._spend(connection, verified, "swap", input_keyset.id)
            signatures = self._sign_outputs(
                connection,
                outputs,
                input_keyset,
                operation="swap",
            )
            self._audit(connection, "swap", input_amount, None, input_keyset.id)
            return signatures

    def retire(self, inputs: list[Proof], memo: str | None) -> dict:
        keyset = self._single_input_keyset(inputs)
        verified = self._verify_inputs(inputs, keyset)
        amount = sum(proof.amount for proof, _ in verified)
        with self._transaction() as connection:
            self._ensure_unspent(connection, verified)
            self._spend(connection, verified, "retire", keyset.id)
            self._audit(connection, "retire", amount, memo, keyset.id)
        return {"amount": amount, "unit": keyset.unit}

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
                "WHERE keyset_id = ? GROUP BY action",
                (self.keyset.id,),
            ).fetchall()
        totals = {row["action"]: row["amount"] for row in rows}
        issued = totals.get("issue", 0)
        retired = totals.get("retire", 0)
        circulating = issued - retired
        return {
            "unit": self.keyset.unit,
            "keyset_id": self.keyset.id,
            "issued": issued,
            "retired": retired,
            "circulating": circulating,
            "outstanding": circulating,
        }

    def add_treasurer(self, npub: str) -> dict:
        normalized = self._normalize_npub(npub)
        now = self._now()
        with self._transaction() as connection:
            existing = connection.execute(
                "SELECT * FROM treasurers WHERE npub = ?", (normalized,)
            ).fetchone()
            if existing is None:
                connection.execute(
                    "INSERT INTO treasurers VALUES (?, 'active', ?, ?, NULL)",
                    (normalized, now, now),
                )
                self._audit(connection, "treasurer:add", 0, normalized)
                created = True
            elif existing["status"] == "active":
                created = False
            else:
                connection.execute(
                    "UPDATE treasurers SET status = 'active', updated_at = ?, "
                    "removed_at = NULL WHERE npub = ?",
                    (now, normalized),
                )
                self._audit(connection, "treasurer:add", 0, normalized)
                created = True
        result = self.get_treasurer(normalized)
        result["created"] = created
        return result

    def get_treasurer(self, npub: str) -> dict:
        normalized = self._normalize_npub(npub)
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM treasurers WHERE npub = ?", (normalized,)
            ).fetchone()
        if row is None:
            raise ClearError("treasurer not found")
        return self._treasurer_response(row)

    def list_treasurers(self) -> dict:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM treasurers ORDER BY added_at, npub"
            ).fetchall()
        return {"treasurers": [self._treasurer_response(row) for row in rows]}

    def grant_treasurer(self, npub: str) -> dict:
        normalized = self._normalize_npub(npub)
        now = self._now()
        with self._transaction() as connection:
            treasurer = connection.execute(
                "SELECT * FROM treasurers WHERE npub = ?", (normalized,)
            ).fetchone()
            if treasurer is None or treasurer["status"] != "active":
                raise ClearError("treasurer must be active before grant")
            consumed = connection.execute(
                "SELECT * FROM treasurer_grants "
                "WHERE npub = ? AND keyset_id IS NOT NULL "
                "ORDER BY consumed_at DESC LIMIT 1",
                (normalized,),
            ).fetchone()
            if consumed is not None:
                raise ClearError("treasurer grant has already created a CMU")
            pending = connection.execute(
                "SELECT * FROM treasurer_grants "
                "WHERE npub = ? AND status = 'pending' "
                "ORDER BY created_at DESC LIMIT 1",
                (normalized,),
            ).fetchone()
            if pending is not None:
                raise ClearError("treasurer already has an unused grant")
            grant_id = str(uuid.uuid4())
            connection.execute(
                "INSERT INTO treasurer_grants VALUES "
                "(?, ?, 'keyset:create', 1, 0, 'pending', ?, ?, NULL, NULL)",
                (grant_id, normalized, now, now),
            )
            self._audit(connection, "treasurer:grant", 0, grant_id)
        return self.get_treasurer_grant(grant_id)

    def get_treasurer_grant(self, grant_id: str) -> dict:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM treasurer_grants WHERE id = ?", (grant_id,)
            ).fetchone()
        if row is None:
            raise ClearError("treasurer grant not found")
        return self._grant_response(row)

    def list_treasurer_grants(self) -> dict:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM treasurer_grants ORDER BY created_at, id"
            ).fetchall()
        return {"grants": [self._grant_response(row) for row in rows]}

    def consume_treasurer_grant(self, grant_id: str, keyset_id: str) -> dict:
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT * FROM treasurer_grants WHERE id = ?", (grant_id,)
            ).fetchone()
            if row is None:
                raise ClearError("treasurer grant not found")
            if row["status"] != "pending":
                raise ClearError("treasurer grant is not pending")
            consumed = connection.execute(
                "SELECT 1 FROM treasurer_grants "
                "WHERE npub = ? AND keyset_id IS NOT NULL",
                (row["npub"],),
            ).fetchone()
            if consumed is not None:
                raise ClearError("treasurer grant has already created a CMU")
            now = self._now(row["updated_at"])
            connection.execute(
                "UPDATE treasurer_grants SET uses = 1, status = 'consumed', "
                "updated_at = ?, consumed_at = ?, keyset_id = ? WHERE id = ?",
                (now, now, keyset_id, grant_id),
            )
            self._audit(connection, "treasurer:grant-consume", 0, grant_id)
        return self.get_treasurer_grant(grant_id)

    def create_cmu(self, grant_id: str, friendly_name: str | None = None) -> dict:
        keyset, secret = Keyset.random(max_order=len(self.keyset.public_keys) - 1)
        encrypted_secret = self._encrypt_keyset_secret(secret)
        now = self._now()
        with self._transaction() as connection:
            grant = self._pending_cmu_grant(connection, grant_id)
            cmu = self._create_cmu_with_connection(
                connection,
                grant,
                keyset,
                encrypted_secret,
                now,
                friendly_name=friendly_name,
            )
        self.keysets[keyset.id] = keyset
        self.keyset_order.append(keyset.id)
        return cmu

    def create_cmu_from_treasury_envelope(
        self,
        envelope: dict,
        *,
        mint_url: str,
    ) -> dict:
        try:
            payload, event = verify_envelope(
                envelope,
                expected_action="cmu:create",
                expected_mint=mint_url,
            )
        except TreasuryAuthError as exc:
            raise ClearError(str(exc)) from exc
        grant_id = payload.get("grant_id")
        if not isinstance(grant_id, str) or not grant_id:
            raise ClearError("treasury request grant_id is missing")
        friendly_name = payload.get("name")
        if friendly_name is not None and not isinstance(friendly_name, str):
            raise ClearError("treasury request CMU name must be a string")
        keyset, secret = Keyset.random(max_order=len(self.keyset.public_keys) - 1)
        encrypted_secret = self._encrypt_keyset_secret(secret)
        now = self._now()
        with self._transaction() as connection:
            grant = self._pending_cmu_grant(connection, grant_id)
            if not self._grant_matches_pubkey(grant["npub"], event["pubkey"]):
                raise ClearError("treasury signature does not match grant treasurer")
            if connection.execute(
                "SELECT 1 FROM treasury_nonces WHERE nonce = ?",
                (payload["nonce"],),
            ).fetchone():
                raise ClearError("treasury request nonce has already been used")
            connection.execute(
                "INSERT INTO treasury_nonces VALUES (?, ?, ?, ?)",
                (payload["nonce"], event["pubkey"], payload["action"], now),
            )
            cmu = self._create_cmu_with_connection(
                connection,
                grant,
                keyset,
                encrypted_secret,
                now,
                friendly_name=friendly_name,
                action="cmu:create:treasury",
            )
        self.keysets[keyset.id] = keyset
        self.keyset_order.append(keyset.id)
        return cmu

    def _pending_cmu_grant(self, connection, grant_id: str):
        grant = connection.execute(
            "SELECT * FROM treasurer_grants WHERE id = ?", (grant_id,)
        ).fetchone()
        if grant is None:
            raise ClearError("treasurer grant not found")
        if grant["status"] != "pending":
            raise ClearError("treasurer grant is not pending")
        treasurer = connection.execute(
            "SELECT * FROM treasurers WHERE npub = ?", (grant["npub"],)
        ).fetchone()
        if treasurer is None or treasurer["status"] != "active":
            raise ClearError("treasurer must be active before CMU creation")
        consumed = connection.execute(
            "SELECT 1 FROM treasurer_grants WHERE npub = ? AND keyset_id IS NOT NULL",
            (grant["npub"],),
        ).fetchone()
        if consumed is not None:
            raise ClearError("treasurer grant has already created a CMU")
        return grant

    @staticmethod
    def _grant_matches_pubkey(grant_npub: str, pubkey: str) -> bool:
        if len(grant_npub) == 64:
            return grant_npub.lower() == pubkey.lower()
        try:
            return npub_to_hex(grant_npub) == pubkey.lower()
        except TreasuryAuthError:
            return False

    def _create_cmu_with_connection(
        self,
        connection,
        grant,
        keyset: Keyset,
        encrypted_secret: str,
        now: int,
        *,
        friendly_name: str | None,
        action: str = "cmu:create",
    ) -> dict:
        connection.execute(
            """
            INSERT INTO cmus(
                keyset_id, unit, fingerprint, status, friendly_name,
                treasurer_npub, material_kind, encrypted_secret, public_keys,
                max_order, created_at, activated_at
            )
            VALUES (?, ?, ?, 'active', ?, ?, 'random-encrypted-v1', ?, ?, ?, ?, ?)
            """,
            (
                keyset.id,
                keyset.unit,
                keyset.fingerprint,
                friendly_name,
                grant["npub"],
                encrypted_secret,
                json.dumps(keyset.public_keys, sort_keys=True),
                len(keyset.public_keys) - 1,
                now,
                now,
            ),
        )
        updated_at = self._now(grant["updated_at"])
        connection.execute(
            "UPDATE treasurer_grants SET uses = 1, status = 'consumed', "
            "updated_at = ?, consumed_at = ?, keyset_id = ? WHERE id = ?",
            (updated_at, updated_at, keyset.id, grant["id"]),
        )
        self._audit(connection, action, 0, grant["id"], keyset.id)
        return self._cmu_response(
            {
                "unit": keyset.unit,
                "keyset_id": keyset.id,
                "fingerprint": keyset.fingerprint,
                "status": "active",
                "friendly_name": friendly_name,
                "treasurer_npub": grant["npub"],
                "material_kind": "random-encrypted-v1",
                "created_at": now,
                "activated_at": now,
            }
        )

    def get_cmu(self, unit_or_keyset_id: str) -> dict:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM cmus WHERE keyset_id = ? OR unit = ?",
                (unit_or_keyset_id, unit_or_keyset_id),
            ).fetchone()
        if row is None:
            raise ClearError("CMU not found")
        return self._cmu_response(row)

    def list_cmus(self) -> dict:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM cmus ORDER BY created_at, keyset_id"
            ).fetchall()
        return {"cmus": [self._cmu_response(row) for row in rows]}

    @staticmethod
    def _treasurer_response(row) -> dict:
        return {
            "npub": row["npub"],
            "status": row["status"],
            "added_at": row["added_at"],
            "updated_at": row["updated_at"],
            "removed_at": row["removed_at"],
        }

    @staticmethod
    def _grant_response(row) -> dict:
        return {
            "id": row["id"],
            "npub": row["npub"],
            "scope": row["scope"],
            "max_uses": row["max_uses"],
            "uses": row["uses"],
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "consumed_at": row["consumed_at"],
            "keyset_id": row["keyset_id"],
        }

    @staticmethod
    def _cmu_response(row) -> dict:
        return {
            "unit": row["unit"],
            "keyset_id": row["keyset_id"],
            "keyset_fingerprint": row["fingerprint"],
            "status": row["status"],
            "friendly_name": row["friendly_name"],
            "treasurer_npub": row["treasurer_npub"],
            "material_kind": row["material_kind"],
            "created_at": row["created_at"],
            "activated_at": row["activated_at"],
        }

    def _validate_outputs(self, outputs: list[BlindedMessage], keyset: Keyset) -> None:
        if any(output.id != keyset.id for output in outputs):
            raise ClearError("outputs must use this Clear currency's active keyset")
        blinded = [output.blinded_secret for output in outputs]
        if len(blinded) != len(set(blinded)):
            raise ClearError("duplicate blinded outputs are not allowed")
        for output in outputs:
            if output.amount not in keyset.private_keys:
                raise ClearError(f"unsupported denomination: {output.amount}")

    def _sign_outputs(
        self,
        connection,
        outputs,
        keyset: Keyset,
        operation: str,
    ) -> list[dict]:
        for output in outputs:
            if connection.execute(
                "SELECT 1 FROM signed_outputs WHERE b_ = ?",
                (output.blinded_secret,),
            ).fetchone():
                raise ClearError("blinded output has already been signed")
        now = self._now()
        signatures = []
        for output in outputs:
            signature = keyset.sign_blinded(output.amount, output.blinded_secret)
            connection.execute(
                "INSERT INTO signed_outputs VALUES (?, ?, ?, ?, ?, ?)",
                (
                    output.blinded_secret,
                    keyset.id,
                    output.amount,
                    signature,
                    operation,
                    now,
                ),
            )
            signatures.append(
                {"amount": output.amount, "id": keyset.id, "C_": signature}
            )
        return signatures

    def _single_input_keyset(self, inputs: list[Proof]) -> Keyset:
        keyset_ids = {proof.id for proof in inputs}
        if len(keyset_ids) != 1:
            raise ClearError("proofs from another Clear currency cannot be combined")
        keyset = self.keysets.get(next(iter(keyset_ids)))
        if keyset is None:
            raise ClearError("proofs from another Clear currency cannot be combined")
        return keyset

    def _verify_inputs(
        self,
        inputs: list[Proof],
        keyset: Keyset,
    ) -> list[tuple[Proof, str]]:
        verified: list[tuple[Proof, str]] = []
        for proof in inputs:
            try:
                y = keyset.verify_proof(
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

    def _spend(self, connection, verified, reason: str, keyset_id: str) -> None:
        now = self._now()
        connection.executemany(
            "INSERT INTO spent_proofs VALUES (?, ?, ?, ?, ?)",
            [(y, keyset_id, proof.amount, reason, now) for proof, y in verified],
        )

    def _audit(
        self,
        connection,
        action: str,
        amount: int,
        reference: str | None,
        keyset_id: str | None = None,
    ) -> None:
        connection.execute(
            "INSERT INTO audit_log(action, keyset_id, amount, reference, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (action, keyset_id or self.keyset.id, amount, reference, self._now()),
        )
