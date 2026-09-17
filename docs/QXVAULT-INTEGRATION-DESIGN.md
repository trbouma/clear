# QxVault Integration Design

Status: Design note

## Purpose

QxVault is relevant to Clear because it packages a production secrets
management platform with an integrated Hardware Security Module (HSM) and an
OpenBao-compatible application programming interface (API). The paper describes
QxVault as a hardened appliance for organizations that need secret storage,
secret distribution, short-lived credentials, rotation, role-based access
control, high availability, and HSM-backed cryptographic operations without
requiring operators to become HSM specialists.

Clear has a matching operational need. A Clear mint must protect keyset
secrets, service identity keys, operator credentials, database credentials,
transport certificates, and future signing boundaries. The QxVault integration
should therefore fit under Clear's existing custody direction:

```text
local secrets in process
  -> OpenBao-compatible custody provider
  -> HSM-backed operation boundary
  -> policy-aware remote signer for Cashu outputs
```

The goal is not to make QxVault a treasury authority. The goal is to make
QxVault a hardened custody and operations boundary for Clear secrets and, over
time, for narrow cryptographic operations.

## Paper summary

The QxVault paper positions the product around six operational claims:

- It addresses secrets sprawl by centralizing storage, distribution, rotation,
  dynamic credential issuance, and role-based access control.
- It ships as a hardened, production-ready appliance instead of a software
  checklist that the customer must harden manually.
- It exposes OpenBao-compatible APIs, preserving compatibility with OpenBao,
  HashiCorp Vault-style workflows, and existing integrations.
- It includes Crypto4A's QxHSM, described as a quantum-safe, FIPS 140-3 Level 3
  HSM, tightly integrated with the appliance.
- It manages core credentials and cluster certificates without requiring
  operators to touch plaintext cryptographic keys.
- It simplifies high availability (HA) cluster deployment and zero-downtime
  upgrades for an HSM-backed secrets management system.

For Clear, the most important point is the API shape. If QxVault is
OpenBao-compatible, Clear should treat it as an OpenBao custody backend first,
then add QxVault-specific deployment guidance where the integrated HSM and HA
properties change the operational posture.

## Integration principle

Clear should integrate QxVault through the same `KeyCustodyProvider`
abstraction proposed for OpenBao:

```text
Clear policy layer
  -> KeyCustodyProvider
       -> LocalKeyProvider
       -> OpenBaoTransitProvider
       -> QxVaultProvider
       -> FuturePolicySignerProvider
```

The QxVault provider should not fork Clear's authority model. It should expose
the same operation-oriented interface:

- encrypt keyset secret;
- decrypt keyset secret during the interim storage phase;
- rewrap encrypted keyset secret;
- sign Clear service events;
- provide public identity material for commissioning evidence;
- issue short-lived database or infrastructure credentials;
- eventually sign blinded Cashu outputs without returning the keyset secret.

This lets Clear keep one treasury and policy model while supporting local
development, OpenBao deployments, and QxVault deployments behind the same
application boundary.

## Clear secret classes

QxVault should be mapped to Clear's secret classes explicitly.

| Clear material | Current or near-term role | QxVault use |
| --- | --- | --- |
| `CLEAR_KEY_ENCRYPTION_KEY` | Wraps treasurer-created random keyset secrets | Replace with QxVault Transit encryption and rewrap operations |
| Random keyset secret | Parent material for a Clear Mint Unit (CMU) keyset | Store only as QxVault-wrapped ciphertext, then move toward HSM-backed signing |
| `CLEAR_MINT_SERVICE_NSEC` | Nostr service identity for treasury instructions and receipts | Replace with QxVault-backed Ed25519 signing if the compatible API supports it |
| `CLEAR_OPERATOR_TOKEN` | Privileged operator API access | Replace or reduce with short-lived QxVault-issued credentials and local-only surfaces |
| Database credential | Access to Clear persistence | Issue as short-lived dynamic credential where supported |
| TLS or mutual TLS material | Protects Clear-to-QxVault, cluster, and admin channels | Let QxVault manage certificate issuance and rotation where the deployment supports it |
| Treasurer `nsec` | Treasurer authority over CMU operations | Remains outside Clear and outside QxVault unless the treasurer independently chooses a custody product |

The treasurer private key remains a user-side or organization-side authority
key. QxVault may protect mint custody and service keys, but it must not cause
Clear to centralize treasurer authority inside the mint operator's appliance.

## Phase 1: QxVault as OpenBao-compatible Transit

The first integration phase should use QxVault as an OpenBao-compatible Transit
backend for keyset-secret wrapping.

Current local model:

```text
Clear process reads CLEAR_KEY_ENCRYPTION_KEY
Clear encrypts/decrypts random keyset secrets locally
SQLite stores encrypted_secret envelope
```

QxVault Transit model:

```text
Clear authenticates to QxVault
Clear sends random keyset secret to Transit encrypt
SQLite stores QxVault ciphertext envelope
Clear sends ciphertext to Transit decrypt only when policy permits use
```

The persisted envelope should identify QxVault without embedding QxVault
credentials:

```json
{
  "kind": "qxvault-transit-v1",
  "addr": "https://qxvault.example.internal",
  "mount": "transit",
  "key": "clear-keyset-wrap",
  "ciphertext": "bao:v1:...",
  "created_at": 1789570000
}
```

This phase improves custody by removing durable wrapping material from Clear's
environment. It does not yet prevent a compromised Clear process from asking
QxVault to decrypt a keyset that the process is authorized to use. That is
acceptable as a first hardening step, but the design should keep moving toward
operation-based signing.

## Phase 2: rewrap existing CMUs

Clear should support an operator-controlled migration from local encrypted
keyset material to QxVault-wrapped material.

Proposed command:

```text
clear-root cmu rewrap-secrets --from local-v1 --to qxvault-transit-v1
```

The command should:

1. require local operator access and a private operator surface;
2. require treasury operations to be paused or disabled;
3. decrypt each local keyset secret using the existing provider;
4. call QxVault Transit encrypt for the configured wrapping key;
5. update only the encrypted envelope and custody metadata;
6. verify the rewrapped secret derives the same public keyset ID; and
7. emit a non-secret audit report.

Rewrapping must not change the CMU, keyset ID, public keys, issued supply,
spent state, treasurer policy, or outstanding Mint Notes.

## Phase 3: service identity signing

The mint service identity should move from a raw `nsec` in the Clear runtime to
an external signing operation when the QxVault-compatible API supports the
required signing mode.

Target flow:

```text
Clear builds unsigned service or receipt event
  -> QxVault signs with named Ed25519 key
  -> Clear attaches signature and records or publishes the event
```

The public key returned by QxVault should be pinned into commissioning evidence
and root-signed service records. Rotating the service signing key must not
change the currency root, treasurer policy, keyset identity, CMU, or existing
Mint Notes.

## Phase 4: dynamic infrastructure credentials

The paper emphasizes short-lived, just-in-time credentials and existing system
integrations. Clear should use that capability for deployment credentials before
using it for monetary authority.

Good candidates:

- database credentials for Clear persistence;
- credentials used by backup and restore jobs;
- internal mutual Transport Layer Security (mTLS) certificates;
- QxVault access tokens delivered through a workload identity or agent sink;
- operator maintenance credentials with narrow time windows.

This reduces long-lived secrets in environment variables and compose files
without changing Clear's public protocol.

## Phase 5: policy-aware Cashu signing

The strongest integration is not merely "store the keyset secret in QxVault."
It is "perform the Cashu signing operation inside a boundary that never returns
the keyset secret."

Target flow:

```text
treasurer signs issuance authorization
  -> Clear verifies policy, grant, limits, nonce, and supply state
  -> Clear submits bounded signing request to QxVault-backed signer
  -> signer validates keyset and request context
  -> signer signs blinded messages
  -> signer emits independent audit evidence
```

This may require a Clear-specific plugin or signing service beside QxVault if
the OpenBao-compatible API cannot directly perform Cashu denomination signing.
The important boundary is that Clear asks for an operation, not a raw key.

The signer should enforce:

- keyset lifecycle state;
- exact `cmu-<keyset-id>` binding;
- authorized denomination vector;
- unique operation identifier;
- treasury authorization evidence hash;
- optional issuance ceilings or time windows;
- caller identity and allowed Clear instance; and
- independent audit logging.

## Deployment shape

A production deployment should keep QxVault on a private administrative network
and expose only Clear's public mint surface externally.

```text
public clients
  -> Clear public API
       -> Clear policy and proof-state layer
            -> QxVault private API
                 -> integrated QxHSM
```

Operator and treasury administration should use separate surfaces:

```text
treasurer wallet
  -> signed encrypted instruction
  -> Clear treasury endpoint
  -> policy verification
  -> QxVault custody operation
```

QxVault availability becomes part of Clear mint availability. Clear should
therefore fail closed when QxVault is unreachable for signing, decrypting, or
credential issuance. Read-only public metadata may remain available, but
issuance, swaps requiring signer access, redemption, and retirement should not
pretend to be final without the required custody operation.

## Configuration sketch

Clear should avoid QxVault-specific assumptions in the public protocol. The
configuration can specialize the custody backend:

```text
CLEAR_KEY_PROVIDER=qxvault-transit
CLEAR_QXVAULT_ADDR=https://qxvault.example.internal
CLEAR_QXVAULT_TOKEN_FILE=/run/secrets/clear-qxvault-token
CLEAR_QXVAULT_TRANSIT_MOUNT=transit
CLEAR_QXVAULT_KEYSET_WRAP_KEY=clear-keyset-wrap
CLEAR_QXVAULT_SERVICE_SIGN_KEY=clear-service-identity
CLEAR_QXVAULT_TLS_CA_FILE=/run/secrets/qxvault-ca.pem
```

Tokens, plaintext keyset secrets, raw service private keys, Transit plaintexts,
and returned dynamic credentials must be redacted from logs and diagnostics.

## Operational requirements

A QxVault-backed Clear deployment needs runbooks for:

- initial appliance trust and certificate pinning;
- Clear workload authentication to QxVault;
- key creation and naming conventions;
- QxVault cluster health checks before Clear startup;
- backup and restore ordering across Clear database and QxVault state;
- disaster recovery when QxVault is unavailable;
- rewrapping and key version rotation;
- incident response for suspected Clear process compromise;
- incident response for suspected QxVault credential compromise; and
- evidence capture for auditors without exposing bearer proofs or key material.

The backup rule is especially important: a Clear database backup without the
corresponding QxVault key state may be unable to operate active CMUs, while a
QxVault backup without Clear's ledger and spent-proof state is not enough to
reconstruct a mint safely.

## Security considerations

- QxVault strengthens custody but does not replace Clear's treasury policy
  checks.
- OpenBao-compatible decrypt is still a powerful capability; prefer signing
  operations that never return keyset secrets.
- QxVault outage should stop supply-changing activity rather than trigger a
  local-secret fallback in production.
- Clear must bind every custody operation to the exact keyset ID and CMU.
- The mint operator must not receive treasurer `nsec` material as part of a
  QxVault deployment.
- HSM-backed storage does not solve double-spend state, issuance accounting,
  replay prevention, or redemption policy by itself.
- QxVault cluster recovery must avoid split-brain signing where two Clear
  instances can independently sign for the same active CMU without shared
  proof-state controls.

## First implementation slice

The useful first slice is intentionally narrow:

1. Add a `KeyCustodyProvider` interface if it is not already present.
2. Implement `LocalKeyProvider` behind the same interface to preserve current
   behavior.
3. Implement `QxVaultTransitProvider` using OpenBao-compatible encrypt,
   decrypt, and rewrap operations.
4. Persist `qxvault-transit-v1` custody envelopes for new random keysets.
5. Add a root-only rewrap command for existing local envelopes.
6. Add tests that prove rewrapping does not change keyset ID, CMU, public
   keys, supply state, or outstanding proof validity.

This gives Clear a practical QxVault integration while leaving room for the
more important long-term move: HSM-backed operation signing instead of
application-held key material.

## Open questions

- Which QxVault API endpoints exactly match OpenBao Transit for encrypt,
  decrypt, key versioning, and Ed25519 signing?
- Can QxVault load a Clear-specific plugin or policy signer near the HSM
  boundary?
- What is the recommended QxVault workload identity mechanism for containerized
  Clear deployments?
- How should Clear coordinate database backups with QxVault cluster snapshots?
- Can QxVault expose audit records that include operation identifiers without
  logging blinded messages, proofs, or bearer secrets?
- What latency and availability profile should Clear assume for online swaps
  and redemption when every signing operation crosses the QxVault boundary?

