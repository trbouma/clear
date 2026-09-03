# Treasurer-Authorized Random Keysets

Status: Accepted target model

## Decision

Every new Clear keyset will be generated from its own cryptographically random
secret inside the mint. A treasurer authorizes creation, but the keyset secret
remains in mint custody during normal operation.

`CLEAR_MASTER_SECRET` will no longer define the identity of new keysets. During
the transition it continues to support the existing deterministic prototype.
In the target model, a separately named mint encryption key protects persisted
random keyset secrets at rest.

```text
root authority appoints treasurer
  -> clear-root records a bounded keyset:create grant
  -> treasurer signs one keyset-creation request
  -> mint validates and consumes the grant
  -> mint generates a random keyset secret internally
  -> mint derives denomination keys and canonical CMU
  -> encrypted secret and authorization evidence are persisted atomically
```

## Authority and custody

Clear distinguishes authority from custody:

- the root authority determines who may act as a treasurer;
- the treasurer authorizes creation and subsequent supply-changing actions;
- the mint has operational custody of the keyset secret; and
- the operational signer uses the secret only after policy checks succeed.

A treasurer does not receive the raw keyset secret merely by authorizing its
creation. A mint operator does not gain governance authority merely because the
running service can access encrypted key material.

The mint operator remains the custodian of the operational keyset secret. That
includes safeguarding the key-encryption material, encrypted keyset-secret rows,
database backups, host/container access, and any runtime environment capable of
decrypting the secret and signing blinded outputs.

The keyset secret is not rotated for an existing CMU. A different keyset secret
derives a different public keyset ID and therefore a different CMU. Treasurer
`npub` rotation changes authority only; it does not change the mint-held signing
material.

The treasurer private key (`nsec`) remains outside Clear. The mint records and
verifies only the treasurer public key (`npub`) or its normalized public-key
form. No Clear configuration file, database row, API request, log entry, backup,
or operator command should contain a treasurer `nsec`.

The initial implementation may use `clear-root` and the operator token to
add or remove treasurer public keys. This is an explicitly privileged
bootstrap registry. A root-signed policy replaces that boundary in the
production governance model.

## Bounded creation grants

The default `keyset:create` grant is single-use. Enrolling a treasurer does not
grant an unlimited ability to create CMUs.

A grant records:

- a unique grant identifier;
- the treasurer's normalized public key;
- the `keyset:create` scope;
- maximum successful uses, initially one;
- issue and expiry times;
- the granting authority and audit reference; and
- consumed time and resulting keyset ID, when used.

In the first release, `clear-root treasurer grant <npub>` sets up one
keyset/CMU creation path for that treasurer. The grant is consumed when the
keyset is created. If that treasurer `npub` has already produced a keyset, a
second grant for the same active treasurer must fail instead of creating
another CMU.

Keyset rotation requires an explicit future procedure. In the first release,
one treasurer identity authorizes at most one CMU at a time; allowing one
treasurer identity to authorize multiple CMUs is deferred until explicit
selection and policy rules exist.

Removing a treasurer prevents future authorizations. It does not invalidate a
keyset already created, alter its CMU, or invalidate its circulating Mint
Notes.

Replacing the authorized treasurer `npub` for an existing CMU is treasurer
authority rotation, not keyset rotation. It changes who may authorize future
actions for that CMU, but it does not change the keyset, CMU, ledger, wallet
balance identity, or existing Mint Notes.

The first-release operator command must require both the old and new public
keys:

```text
clear-root cmu rotate-treasurer cmu-<keyset-id> \
  --old-npub npub1old... \
  --new-npub npub1new... \
  --reason <text>
```

The mint must reject the rotation if `--old-npub` does not match the CMU's
current authority record.

## Keyset generation

The mint generates at least 256 bits of randomness for each keyset. That
random keyset secret is the independent parent material from which its
denomination keys are derived.

The keyset ID is calculated from the resulting public keys using the applicable
Cashu keyset-ID rules. The Clear Mint Unit remains bound to that public keyset:

```text
cmu-<keyset-id>
```

The creation transaction must atomically persist:

- encrypted keyset secret;
- encryption format and key version;
- public denomination keys;
- keyset ID and CMU;
- maximum denomination order;
- authorizing treasurer and signed request;
- consumed grant and replay-prevention nonce;
- creation time; and
- initial lifecycle status.

If persistence fails, the keyset is not activated or advertised.

## Secret protection

Random keyset secrets must be encrypted at rest with authenticated encryption.
The mint's key-encryption key is operational infrastructure secret material; it
is not a currency identity and must not be used directly as a Cashu signing
key.

The encryption design must support key rotation without changing the protected
keysets. Rewrapping a keyset secret changes its encrypted representation, not
its public keys, keyset ID, CMU, or Mint Notes.

Logs, API responses, audit events, exception messages, database exports, and
routine backups must never contain an unencrypted keyset secret.

## Lifecycle

Each persisted keyset has an explicit state:

| State | Meaning |
| --- | --- |
| `active` | New issuance, swaps, proof checks, redemption, and retirement are allowed under policy. |
| `redemption-only` | New issuance is blocked; existing notes can still be validated, refreshed as policy allows, redeemed, or retired. |
| `suspended` | Operations fail closed while an incident or policy question is resolved. |
| `migrating` | Supply-changing activity is frozen while state is transferred. |
| `retired` | The keyset no longer operates, subject to its published terminal policy. |

Creating a successor keyset creates a new CMU. It does not silently continue
or merge the old balance.

Whole-CMU lifecycle transitions use an explicit `clear-root cmu` command group,
for example `clear-root cmu suspend`, `clear-root cmu redemption-only`, and
`clear-root cmu retire`. The top-level `clear-root retire` command remains
reserved for retiring presented Mint Notes, amounts, tokens, or proofs from
circulation.

## Migration

Migration is an exceptional custody transfer, not an ordinary treasurer
operation. It requires explicit authorization, source-operator confirmation,
a frozen source keyset, and an identified destination.

The migration package contains only the selected keyset's material and state:

- the random keyset secret;
- public descriptor and lifecycle metadata;
- complete issuance and retirement checkpoints;
- spent-proof state;
- consumed authorization state; and
- audit-chain continuity evidence.

The package must be authenticated and encrypted directly to the destination
mint or designated recovery custodian. It must never include the mint's
key-encryption key or secrets for any other keyset.

A treasurer authorizes migration but does not automatically receive the
secret. The treasurer receives key material only when the approved destination
is explicitly a treasurer-controlled custodian.

The source must not resume independent signing after successful migration.
Preventing split-brain operation requires a migration protocol and operational
controls in addition to encrypting the package.

## Security boundary

Software authorization alone cannot stop a fully compromised process that can
decrypt an operational keyset secret. The first implementation provides
policy verification, encrypted storage, bounded grants, replay protection, and
complete audit evidence.

Stronger enforcement should move signing into an HSM or remote signer that
requires a valid treasurer authorization before using the keyset. This changes
the compromise boundary without changing keyset identity or the public
protocol.

## Compatibility and transition

Existing master-derived keysets remain valid legacy keysets. Their public keys,
keyset IDs, CMUs, proofs, and ledgers must not change.

Implementation should identify key material by version, for example:

```text
legacy-derived-v1
random-encrypted-v2
```

New random keysets must be introduced through a database migration and explicit
creation workflow. Clear must not generate a new random keyset merely because
the process restarted or a database field was absent.

## Initial command model

The prototype remains consolidated under `clear-root`:

```text
clear-root treasurer keygen
clear-root treasurer add <npub>
clear-root treasurer remove <npub>
clear-root treasurer list
clear-root treasurer grant <npub>
clear-root treasurer grants
clear-root cmu create <grant-id> --name <name>
clear-root cmu list
```

`clear-root` is a local mint-administration command. It uses
`CLEAR_ROOT_API_URL`, accepts only loopback addresses, and is expected to run
inside the mint container or another trusted environment with access to local
configuration and storage. The operator API independently rejects
non-loopback clients, even when they present the correct bearer token.

The treasurer private key never enters mint configuration. A future extracted
treasury CLI can create and sign the authorization while preserving the same
request and audit formats.

`clear-root treasurer keygen` is a local convenience command only. It may be
used for development or assisted onboarding, but it does not store the keypair
or submit the `nsec` to the mint. In separated custody, the treasurer should
generate and retain their own `nsec`.

In the first-release treasury CLI flow, the treasurer's `nsec` derives an
`npub`, and the mint resolves that `npub` to exactly one CMU. If the `npub` is
unknown, rotated out, suspended, or ambiguously associated with more than one
CMU, the command fails closed.
