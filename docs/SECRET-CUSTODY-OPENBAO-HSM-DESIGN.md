# Secret Custody with OpenBao and HSMs

Status: Design note

## Purpose

Clear currently relies on locally supplied secret material for mint identity,
keyset custody, and privileged operator access. That is acceptable for
development and early controlled deployments, but it leaves too much authority
inside the application process. A compromised Clear runtime with access to
the right environment variables can compromise the mint.

This note describes a migration path from local environment secrets to an
operation-based custody model:

```text
local secrets in process
  -> OpenBao Transit for encryption and signing operations
  -> HSM-backed OpenBao or direct HSM-backed signing boundaries
```

The goal is to move Clear from "read a secret and use it locally" toward
"ask a custody service to perform a narrow cryptographic operation."

## Secret classes

Clear has several secret classes with different blast radii.

| Secret | Current role | Compromise impact | Target custody |
| --- | --- | --- | --- |
| `CLEAR_MASTER_SECRET` | Legacy root-derived keyset material | Can recreate legacy operator keyset identity and signing material | Retire from new keysets; protect only for legacy restore |
| `CLEAR_KEY_ENCRYPTION_KEY` | Wraps treasurer-created random keyset secrets | Can decrypt random keyset secrets from the database | Replace with OpenBao Transit encrypt/decrypt |
| Random keyset secret | Parent material for a CMU keyset | Can sign valid Mint Notes outside policy if exposed | Never expose to app long term; remote signer or HSM boundary |
| `CLEAR_MINT_SERVICE_NSEC` | Stable mint service identity | Can sign service identity and commissioning evidence | OpenBao/HSM signing operation |
| `CLEAR_OPERATOR_TOKEN` | Privileged local operator API access | Enables privileged root operations while accepted | Short-lived scoped auth, local-only operator surface, or mTLS/OIDC-backed operator auth |
| Treasurer `nsec` | Treasurer authority over CMU operations | Can authorize actions for assigned CMUs | Remains outside mint; treasurer-side wallet custody |

The treasurer `nsec` is not mint custody material. It authorizes policy
actions; it does not derive or decrypt keyset secrets.

## Design principle

Clear should introduce a key custody abstraction before binding itself to a
specific secret manager or HSM.

```text
Clear policy layer
  -> KeyCustodyProvider
       -> LocalKeyProvider
       -> OpenBaoTransitProvider
       -> FutureHsmProvider
```

The application should request operations, not raw keys:

- encrypt keyset secret;
- decrypt keyset secret, as an interim step;
- rewrap encrypted keyset secret;
- sign service event;
- derive or return public identity;
- eventually sign blinded Cashu outputs without returning keyset secret.

The same policy code should run regardless of the custody backend. The backend
changes where key material lives and which operation boundary is enforced.

## OpenBao Transit first step

OpenBao Transit is the best first backend because it provides cryptographic
operations over HTTP while keeping named keys inside OpenBao. Transit supports
encryption/decryption, HMAC, random bytes, and signing key types such as
Ed25519. It is therefore suitable for replacing local key-encryption material
before introducing a hardware security module.

### Phase 1: protect keyset-secret encryption

The first production hardening target should be
`CLEAR_KEY_ENCRYPTION_KEY`.

Current model:

```text
Clear process reads CLEAR_KEY_ENCRYPTION_KEY
Clear process encrypts/decrypts random keyset secrets locally
SQLite stores encrypted_secret envelope
```

OpenBao Transit model:

```text
Clear process authenticates to OpenBao
Clear sends random keyset secret to transit/encrypt
SQLite stores OpenBao ciphertext envelope
Clear sends ciphertext to transit/decrypt only when policy permits signing
```

This keeps the wrapping key out of the Clear environment and gives operators
a separate place to rotate, audit, and revoke access. It does not yet protect
against a compromised Clear process that is allowed to call decrypt, but it
removes a durable secret from the deployment environment and establishes the
provider boundary.

The persisted envelope should identify the backend and key version:

```json
{
  "kind": "openbao-transit-v1",
  "mount": "transit",
  "key": "clear-keyset-wrap",
  "ciphertext": "bao:v1:...",
  "created_at": 1789570000
}
```

The envelope must not include an OpenBao token, unencrypted keyset secret, or
operator credential.

### Phase 2: rewrap existing random keysets

Clear should add a root-only rewrap command:

```text
clear-root cmu rewrap-secrets --from local-v1 --to openbao-transit-v1
```

The command should:

1. require operator access and loopback execution;
2. require treasury operations to be disabled;
3. decrypt each local `random-encrypted-v1` keyset secret;
4. call OpenBao Transit encrypt with the configured wrapping key;
5. update only the encrypted envelope and material metadata;
6. verify each rewrapped keyset can still derive the same public keys; and
7. emit a non-secret audit report.

Rewrapping must not change the keyset ID, CMU id, public keys, issued supply,
spent state, treasurer, or outstanding Mint Notes.

### Phase 3: service identity signing

The mint service identity should move from `CLEAR_MINT_SERVICE_NSEC` to an
external signer:

```text
Clear builds unsigned Nostr/service event
  -> OpenBao signs with named Ed25519 key
  -> Clear attaches signature and publishes/records evidence
```

This requires the signing library path to support external signing rather than
requiring an in-process `nsec`. The service public key should be read from the
custody provider and pinned into commissioning evidence.

## Remote signer and HSM direction

OpenBao Transit reduces local secret exposure, but Transit decrypt is still
powerful. If a compromised Clear process can request decrypt for any active
keyset, it can recover keyset secrets during runtime.

The stronger design is a remote signing boundary:

```text
Clear verifies request policy, treasury authorization, and supply state
Clear sends bounded signing request to signer
Signer validates request context and signs blinded messages
Signer never returns keyset secret
Signer emits independent audit event
```

The signer should enforce at least:

- keyset status is active or redemption-only as appropriate;
- request is authenticated from an allowed Clear instance;
- keyset id and CMU id match the configured signer key;
- request has a unique nonce or operation id;
- amount vector and outputs match the authorized operation;
- optional issuance ceilings or budget windows; and
- treasury readiness is current.

An HSM can enter this architecture in two ways:

1. OpenBao is HSM-backed for seal/unseal or managed key operations.
2. Clear or a Clear signer talks directly to a PKCS#11/KMS-backed signing
   service.

The first option is operationally simpler. The second option provides a more
direct policy-enforcing boundary for Cashu signing, but it requires more Clear
specific signer design.

## Configuration shape

Clear should move from raw secret configuration to custody configuration.

Example:

```text
CLEAR_KEY_PROVIDER=openbao-transit
CLEAR_OPENBAO_ADDR=https://bao.example.internal
CLEAR_OPENBAO_TOKEN_FILE=/run/secrets/clear-openbao-token
CLEAR_OPENBAO_TRANSIT_MOUNT=transit
CLEAR_OPENBAO_KEYSET_WRAP_KEY=clear-keyset-wrap
CLEAR_OPENBAO_SERVICE_SIGN_KEY=clear-service-identity
```

The OpenBao token should be read from a file, workload identity, or short-lived
agent sink, not supplied on the command line. Logs and diagnostics must redact
the token, ciphertext plaintexts, event private keys, and raw keyset secrets.

## OpenBao policy sketch

The Clear runtime token should receive only the operations it needs.

For phase 1, the token needs encrypt/decrypt on one wrapping key:

```text
path "transit/encrypt/clear-keyset-wrap" {
  capabilities = ["update"]
}

path "transit/decrypt/clear-keyset-wrap" {
  capabilities = ["update"]
}
```

An operator rewrap token may also need read access to key metadata and rotate
or rewrap permissions, but that should be a separate operational role.

For service identity signing, grant only sign access to the service key:

```text
path "transit/sign/clear-service-identity" {
  capabilities = ["update"]
}
```

Clear should not require export permissions for production keys.

## Runtime behavior

Clear should fail closed when a configured custody backend is unavailable.

- Startup should verify custody backend health for required operations.
- `clear-root verify` should include custody checks without exposing secrets.
- Treasury enablement should require successful custody checks.
- If OpenBao is unavailable, new issuance and swaps should fail closed.
- Read-only metadata endpoints can remain available.
- Incident logs should identify the failed operation and key name, not the
  plaintext or token.

For a remote signing phase, failed signer health should disable treasury
mutations for affected CMUs until the operator verifies recovery.

## Rotation and recovery

Different keys rotate differently.

| Material | Rotation model |
| --- | --- |
| OpenBao wrapping key | Rotate named Transit key version and rewrap envelopes when needed |
| Random keyset secret | Not rotated in place; a new secret creates a new keyset/CMU |
| Service signing key | Rotate service identity through explicit commissioning evidence |
| Operator token | Revoke and reissue without changing CMUs |
| Treasurer key | Rotate CMU authority record without changing keyset identity |

Backups must include:

- Clear database;
- OpenBao storage or OpenBao disaster-recovery backup;
- OpenBao unseal or recovery procedure;
- key names and policy configuration;
- service commissioning evidence; and
- non-secret rewrap/audit reports.

Backups must not collect OpenBao runtime tokens, raw keyset secrets, or
treasurer `nsec`s.

## Audit requirements

Each custody operation should produce enough non-secret evidence to answer:

- which key or CMU was used;
- which Clear instance requested the operation;
- which authenticated actor or workload identity was used;
- which policy action required it;
- when it happened;
- whether it succeeded; and
- which audit sequence or request id links it to Clear's ledger event.

Audit logs should correlate with Clear issuance, swap, retirement, treasury
grant, and commissioning records. They should not reveal blinded secrets,
proof secrets, bearer tokens, raw keyset secrets, OpenBao tokens, or `nsec`s.

## Implementation plan

1. Define a `KeyCustodyProvider` interface for encrypt/decrypt and service
   signing.
2. Move current local encryption into `LocalKeyProvider` without changing
   stored data.
3. Add `OpenBaoTransitProvider` and `openbao-transit-v1` envelopes.
4. Add startup and `clear-root verify` custody health checks.
5. Add root-only rewrap tooling from local envelopes to OpenBao envelopes.
6. Move `CLEAR_MINT_SERVICE_NSEC` to an external signer path.
7. Add optional remote Cashu signer protocol for active keysets.
8. Evaluate HSM-backed OpenBao or direct PKCS#11 signer integration.

## Non-goals

This design does not:

- make a compromised treasurer `nsec` harmless;
- make active-active mint operation safe;
- rotate an existing CMU's keyset secret in place;
- remove the need for database backups and restore drills;
- define a complete HSM signer protocol; or
- prove OpenBao policy is correct for a given deployment.

It creates the boundary needed for those later controls to be introduced
without changing Clear's public CMU identity model.

## References

- OpenBao Transit secrets engine:
  <https://openbao.org/docs/secrets/transit/>
- OpenBao Transit API:
  <https://openbao.org/docs/next/api/secret/transit/>
- OpenBao PKCS#11 seal:
  <https://openbao.org/docs/configuration/seal/pkcs11/>
- Existing Clear random-keyset model:
  `docs/TREASURER-AUTHORIZED-RANDOM-KEYSETS-DESIGN.md`
- Existing Clear devops recommendations:
  `docs/CLEAR-DEVOPS-RECOMMENDATIONS.md`
