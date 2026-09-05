# Clear Mint Data Schema

Status: Current implementation note

This document describes the SQLite data schema used by the Clear mint, how
records are separated for each Clear Mint Unit (CMU), and what the mint stores
or generates for keysets.

Clear currently stores all CMUs for one mint deployment in one SQLite database.
Separation is logical, not one database file per CMU. Every supply-changing
record is bound to a keyset, and each keyset defines one CMU.

```text
one Clear deployment
  -> one SQLite database
  -> many keyset rows in cmus
  -> one CMU per keyset
  -> issuance, swap, retirement, and audit rows scoped by keyset_id
```

Wallets and applications must keep balances separated by:

```text
mint URL + unit + keyset ID
```

Friendly names and unit aliases are display hints only.

## Identity Model

The current implementation stores both:

- `keyset_id`: the full Cashu keyset identifier used by proofs and key
  discovery; and
- `unit`: the protocol unit string displayed to wallets, currently
  `cmu-<keyset_fingerprint>`.

The keyset fingerprint is derived from the keyset public keys. The full keyset
ID is also derived from the keyset public keys and unit. A CMU row stores both
values so clients can bind display, proofs, and ledger state to the same
underlying keyset.

## Table Summary

| Table | Purpose | CMU separation |
| --- | --- | --- |
| `mint_metadata` | Database schema and root keyset identity binding | Deployment-level |
| `cmus` | CMU registry, display metadata, public keys, and key material metadata | One row per keyset/CMU |
| `treasurers` | Authorized treasurer public keys | One treasurer may be bound to one CMU in the first release |
| `treasurer_grants` | Single-use keyset/CMU creation grants | Consumed grant records resulting `keyset_id` |
| `treasury_nonces` | Replay protection for signed treasury requests | Shared replay set across treasury actions |
| `commissioning_verifications` | Durable root-verification results and non-secret evidence | One row per verification run |
| `treasury_state` | Fail-closed treasury enablement state | Deployment-level singleton |
| `mint_quotes` | Issuance authorization quotes | Each quote records `keyset_id` and `unit` |
| `issue_batches` | Idempotency records for mint requests | Indirectly scoped by quote |
| `signed_outputs` | Blinded outputs already signed by the mint | Each signed output records `keyset_id` |
| `spent_proofs` | Nullifier/spent-state records | Each spent proof records `keyset_id` |
| `audit_log` | Supply and operator action history | Each audit row records `keyset_id` |

## `mint_metadata`

`mint_metadata` is a small key/value table:

```sql
key TEXT PRIMARY KEY
value TEXT NOT NULL
```

It currently stores:

- `schema_version`;
- root/legacy `keyset_id`;
- root/legacy `keyset_fingerprint`; and
- root/legacy `protocol_unit`.

On startup, Clear checks that the configured root keyset still matches the
database identity. If the configured root keyset differs from the persisted
identity, startup fails instead of silently serving an existing ledger under a
new keyset.

## `cmus`

`cmus` is the CMU and keyset registry:

```sql
keyset_id TEXT PRIMARY KEY
unit TEXT NOT NULL UNIQUE
fingerprint TEXT NOT NULL
status TEXT NOT NULL
friendly_name TEXT
friendly_unit_alias TEXT
treasurer_npub TEXT
material_kind TEXT NOT NULL
encrypted_secret TEXT
public_keys TEXT NOT NULL
max_order INTEGER NOT NULL
created_at INTEGER NOT NULL
activated_at INTEGER
```

Each row represents one keyset and therefore one CMU.

Stored values:

- `keyset_id`: full keyset identifier.
- `unit`: wallet-facing protocol unit, currently `cmu-<fingerprint>`.
- `fingerprint`: short keyset fingerprint used in the unit string.
- `status`: `active` for ordinary CMUs and `commissioning` for inactive,
  test-only verification keysets; future lifecycle states include suspended,
  redemption-only, migrating, and retired.
- `friendly_name`: wallet-facing display name, such as `Food Share Credits`.
- `friendly_unit_alias`: wallet-facing unit label, such as `shares`.
- `treasurer_npub`: authorized treasurer public key for treasurer-created
  CMUs, or `NULL` for the root/legacy CMU.
- `material_kind`: identifies how key material is controlled.
- `encrypted_secret`: encrypted random keyset secret for treasurer-created
  CMUs, or `NULL` for the root/legacy CMU.
- `public_keys`: JSON object of denomination amount to compressed secp256k1
  public key.
- `max_order`: largest power-of-two denomination order in the keyset.
- `created_at` and `activated_at`: Unix timestamps.

`/v1/keysets`, `/v1/keys`, and `/v1/keys/{keyset_id}` are generated from this
registry and include the public keys and display metadata needed by wallets.

## Keyset Material Kinds

Clear currently recognizes three key material kinds.

### `legacy-derived-v1`

The root/legacy keyset is derived at process startup from:

```text
CLEAR_MASTER_SECRET
optional CLEAR_ROOT_AUTHORITY_NPUB
max_order
```

For each supported denomination, Clear derives a private signing key with HMAC:

```text
HMAC-SHA256(
  derivation_secret,
  "clear-keyset-v2:<amount>"
)
```

The digest is reduced to a valid secp256k1 scalar. The matching compressed
public key is stored in `cmus.public_keys`.

For this keyset:

- `material_kind` is `legacy-derived-v1`;
- `encrypted_secret` is `NULL`;
- `treasurer_npub` is `NULL`;
- display labels are populated from `CLEAR_CURRENCY_ALIAS` and
  `CLEAR_CURRENCY_UNIT_ALIAS`; and
- changing `CLEAR_MASTER_SECRET` or `CLEAR_ROOT_AUTHORITY_NPUB` changes the
  root keyset and must not be applied to an existing database.

### `random-encrypted-v1`

Treasurer-created CMUs use independent random keyset secrets generated inside
the mint:

```text
secret = 32 random bytes, hex encoded
```

The random secret is the parent material for the same denomination-key
derivation process used by `legacy-derived-v1`. The raw random secret is not
returned through the API.

For this keyset:

- `material_kind` is `random-encrypted-v1`;
- `treasurer_npub` stores the authorized treasurer public key;
- `public_keys` stores the public denomination keyset descriptor;
- `encrypted_secret` stores an authenticated-encryption envelope; and
- the grant that created it records the resulting `keyset_id`.

The encrypted secret envelope is JSON:

```json
{
  "format": "aes-256-gcm",
  "key_version": "clear-key-encryption-v1",
  "nonce": "<12-byte nonce hex>",
  "ciphertext": "<ciphertext and tag hex>"
}
```

The AES-GCM key is derived from the configured key-encryption material:

```text
SHA256("clear-key-encryption-v1:" + key_encryption_key)
```

The associated data is:

```text
clear-random-keyset-secret-v1
```

In the current app wiring, `CLEAR_KEY_ENCRYPTION_KEY` is preferred when set;
otherwise Clear falls back to `CLEAR_MASTER_SECRET` for development
compatibility. A real deployment should use and back up a separate
`CLEAR_KEY_ENCRYPTION_KEY`.

The treasurer `nsec` is authorization material, not keyset custody material. It
does not derive, decrypt, export, or store this random keyset secret. The mint
operator is responsible for safeguarding the key-encryption material, encrypted
secret envelope, database backups, host/container access, and runtime signing
paths that can decrypt or use the secret.

A compromised treasurer `nsec` can authorize actions for the CMU while that
treasurer remains active. A compromised keyset secret can create valid Mint
Notes outside the ledger and bypass software authorization checks. Those are
different failure modes, and keyset-secret compromise is the deeper
supply-integrity failure.

### `commissioning-random-encrypted-v1`

Commissioning CMUs use the same encrypted random-key mechanism and custody
boundary as `random-encrypted-v1`. Their `material_kind` is
`commissioning-random-encrypted-v1`. They remain inactive for public quote
creation and are retained as verification evidence.

## Treasurer Tables

### `treasurers`

```sql
npub TEXT PRIMARY KEY
status TEXT NOT NULL
added_at INTEGER NOT NULL
updated_at INTEGER NOT NULL
removed_at INTEGER
```

The mint stores treasurer public keys only. A treasurer `nsec` must never be
stored in configuration, the database, logs, backups, or API requests.

In the first release, a treasurer is expected to control at most one active CMU.

### `treasurer_grants`

```sql
id TEXT PRIMARY KEY
npub TEXT NOT NULL
scope TEXT NOT NULL
max_uses INTEGER NOT NULL
uses INTEGER NOT NULL DEFAULT 0
status TEXT NOT NULL
created_at INTEGER NOT NULL
updated_at INTEGER NOT NULL
consumed_at INTEGER
keyset_id TEXT
```

The current grant scope is `keyset:create`. A grant starts as pending, can be
used once, and is consumed when the CMU is created. When consumed, the grant row
records the new `keyset_id`.

The mint rejects a new grant for an active treasurer that has already created a
CMU in the first-release model.

### `treasury_nonces`

```sql
nonce TEXT PRIMARY KEY
pubkey TEXT NOT NULL
action TEXT NOT NULL
created_at INTEGER NOT NULL
```

This table prevents replay of signed treasury envelopes. It is shared across
treasury actions such as:

- `cmu:create`;
- `cmu:info`; and
- `quote:authorize`.

## Commissioning Tables

### `commissioning_verifications`

Each root verification run records its identifier, profile version, status,
configuration fingerprint, Clear version, schema version, commissioning
keyset, timestamps, issued and retired totals, non-secret check evidence, and
an optional failure reason. Evidence is stored as canonical JSON with a digest.

Successful verification requires equal issued and retired totals and zero
outstanding commissioning supply. Failed and superseded runs remain available
for audit. Each run uses a new test-only commissioning CMU.

### `treasury_state`

`treasury_state` is a singleton row containing:

```sql
id INTEGER PRIMARY KEY
enabled INTEGER NOT NULL
verification_id TEXT
reason TEXT NOT NULL
updated_at INTEGER NOT NULL
```

Clear creates this row disabled. Enabling it requires a successful verification
whose configuration fingerprint still matches the running mint. A new
verification, failed verification, explicit disable action, or critical
configuration change closes the gate.

The gate applies to signed CMU creation and signed quote authorization. It does
not block root-local operator recovery, proof-state queries, retirement, or
holder swaps involving existing Mint Notes.

## Issuance Tables

### `mint_quotes`

```sql
id TEXT PRIMARY KEY
keyset_id TEXT NOT NULL
unit TEXT NOT NULL
amount_requested INTEGER NOT NULL
amount_paid INTEGER NOT NULL DEFAULT 0
amount_issued INTEGER NOT NULL DEFAULT 0
memo TEXT
created_at INTEGER NOT NULL
updated_at INTEGER NOT NULL
```

Each quote is bound to a CMU by `keyset_id` and `unit`.

Quote creation resolves the requested `unit` to one known keyset. Operator or
treasurer authorization updates `amount_paid`. Minting consumes authorized
quote capacity by increasing `amount_issued`.

Treasurer issuance works by:

```text
clear-treasury issue
  -> signed cmu:info resolves treasurer key to one active CMU
  -> quote is created for that CMU unit
  -> signed quote:authorize proves treasurer authority
  -> blinded outputs are minted against the quote keyset
```

### `issue_batches`

```sql
request_hash TEXT PRIMARY KEY
quote_id TEXT NOT NULL
amount INTEGER NOT NULL
signatures TEXT NOT NULL
```

This table provides idempotency for mint requests. The request hash is computed
from the quote ID and canonical blinded-output payload. If the same request is
submitted again, Clear returns the same signatures.

`issue_batches` is scoped to a CMU indirectly through `quote_id`, because each
quote records its `keyset_id`.

### `signed_outputs`

```sql
b_ TEXT PRIMARY KEY
keyset_id TEXT NOT NULL
amount INTEGER NOT NULL
c_ TEXT NOT NULL
operation TEXT NOT NULL
created_at INTEGER NOT NULL
```

This table records every blinded output signed by the mint. It prevents the
same blinded output from being signed twice.

Each row records the signing `keyset_id`. This allows inspection by CMU, while
the primary key remains global for the mint database.

## Spent-State Tables

### `spent_proofs`

```sql
y TEXT PRIMARY KEY
keyset_id TEXT NOT NULL
amount INTEGER NOT NULL
reason TEXT NOT NULL
spent_at INTEGER NOT NULL
```

`y` is the proof secret mapped to curve point form. It is the nullifier used for
spent-state checks.

Each spent row records the `keyset_id` of the CMU whose proof was spent. Swaps
and retirements both spend input proofs. A proof can only be verified against
the keyset named by the proof ID, and mixed-keyset input sets are rejected.

Current spend reasons include:

- `swap`; and
- `retire`.

## Audit Table

### `audit_log`

```sql
id INTEGER PRIMARY KEY AUTOINCREMENT
action TEXT NOT NULL
keyset_id TEXT NOT NULL
amount INTEGER NOT NULL
reference TEXT
created_at INTEGER NOT NULL
```

The audit log records supply-changing actions and operator/treasury actions.
Rows are scoped by `keyset_id`.

Current action values include:

- `authorize`;
- `issue`;
- `swap`;
- `retire`;
- `treasurer:add`;
- `treasurer:grant`;
- `treasurer:grant-consume`;
- `cmu:create`;
- `cmu:create:treasury`;
- `cmu:label`;
- `commissioning:start`;
- `commissioning:verified`;
- `commissioning:failed`;
- `treasury:enable`; and
- `treasury:disable`.

The current `clear-root summary` command reports the legacy/root keyset totals.
Per-CMU summary views are a natural follow-on improvement.

## CMU Separation Rules

Clear separates CMU state in these ways:

- The `cmus` table has one row per keyset/CMU.
- Every quote records `keyset_id` and `unit`.
- Issuance uses the quote's `keyset_id`, not the mint's first keyset.
- Signed outputs record the keyset that produced the signature.
- Swap inputs must all belong to one keyset.
- Swap outputs must use the same keyset as the inputs.
- Retire inputs must all belong to one keyset.
- Spent-proof rows record the keyset whose proofs were spent.
- Audit rows record the keyset affected by the action.
- Public key discovery exposes active and inactive keysets separately and marks
  their active state explicitly.

Clear does not currently support cross-CMU swaps or implicit equivalence
between CMUs. If a holder has Mint Notes from two CMUs, those are two separate
balances even when they share the same mint operator or friendly name.

## Shared State Across CMUs

Some state is shared at the deployment level:

- one SQLite database file;
- one `mint_metadata` identity binding for the root/legacy keyset;
- one treasurer registry;
- one nonce replay table;
- one commissioning history and treasury-state singleton;
- one audit table with keyset-scoped rows;
- one public mint URL; and
- one operator API boundary.

This means separation is enforced by schema fields, runtime validation, and
query behavior rather than by separate physical database files.

## Startup Behavior

On startup, Clear:

1. creates tables if needed;
2. records or verifies the schema version;
3. verifies the root/legacy keyset identity against `mint_metadata`;
4. adds any missing display metadata columns;
5. inserts the legacy CMU row if absent;
6. populates legacy display metadata from configuration if unset;
7. decrypts persisted random and commissioning keyset secrets;
8. re-derives their public keys, fingerprints, units, and keyset IDs;
9. creates the fail-closed treasury-state singleton when absent;
10. invalidates enabled readiness when the critical configuration fingerprint
   changes; and
11. refuses startup if persisted keyset identity does not match the decrypted
   secret.

This prevents the mint from silently advertising or signing for a keyset whose
stored descriptor does not match its key material.

## What Is Not Stored

The mint must not store:

- treasurer `nsec` values;
- unencrypted random keyset secrets for treasurer-created CMUs;
- recipient wallet private keys;
- local treasurer wallet proofs, except in the treasurer's own local
  `clear-treasury` wallet file outside the mint database; or
- bearer tokens delivered to recipient wallets, except insofar as their proofs
  later appear as spent nullifiers.

## Operational Notes

Backups of the mint database are sensitive. They include encrypted keyset
secrets, public key descriptors, treasurer authority records, grant history,
issuance records, signed-output records, spent-proof state, and audit history.

For treasurer-created CMUs, a database backup is not sufficient by itself. The
operator also needs the correct key-encryption material, preferably
`CLEAR_KEY_ENCRYPTION_KEY`, to decrypt random keyset secrets after restore.

The mint operator is ultimately responsible for that key-encryption material
and for every environment that can decrypt and use the keyset secret. The
treasurer never needs, receives, or backs up the keyset secret for their CMU.

For the root/legacy CMU, restore requires the same `CLEAR_MASTER_SECRET`, and
if configured, the same `CLEAR_ROOT_AUTHORITY_NPUB`, because the keyset is
derived rather than stored as an encrypted random secret.
