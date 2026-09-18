# QxVault and Clear Analysis

Status: Analysis note

## Purpose

This note analyzes the QxVault whitepaper in relation to Clear. The paper
describes QxVault as a hardened secrets management appliance with
OpenBao-compatible application programming interfaces (APIs), an integrated
Hardware Security Module (HSM), high availability (HA) clustering, automated
credential management, and reduced operational complexity for teams that do not
have deep HSM expertise.

For Clear, QxVault is relevant because a Clear mint is not only an application
server. It is custody infrastructure for issuer-defined, redeemable,
Chaumian bearer instruments. A production Clear deployment must protect:

- per-Clear Mint Unit (CMU) keyset secrets;
- the key-encryption material or custody provider used to protect those
  keysets;
- mint service identity keys;
- operator credentials;
- database credentials;
- transport certificates; and
- audit and recovery material tied to issuance, redemption, and spent-proof
  state.

QxVault should therefore be considered as a custody and operations boundary for
Clear, not as a replacement for Clear's treasury authority model.

## What the paper claims

The whitepaper positions QxVault around a practical deployment problem:
organizations need secrets management, but production-grade secrets management
is itself difficult to deploy, harden, cluster, and operate.

The paper's main claims are:

1. Organizations suffer from secrets sprawl across laptops, configuration
   files, repositories, continuous integration and continuous delivery
   pipelines, cloud systems, and runtime environments.
2. A secrets management system should centralize secret storage, distribute
   secrets to authorized clients, support rotation, issue short-lived
   just-in-time credentials, enforce fine-grained role-based access controls,
   and integrate with existing systems such as databases.
3. A secrets management system is critical infrastructure because other systems
   depend on it to authenticate and operate.
4. Adding an HSM is often recommended or required, but sourcing, provisioning,
   integrating, and maintaining an HSM adds complexity.
5. QxVault combines a production-ready secrets management platform with a
   built-in, quantum-safe, Federal Information Processing Standards (FIPS)
   140-3 Level 3 HSM.
6. QxVault exposes OpenBao-compatible APIs, giving it compatibility with the
   OpenBao, HashiCorp Vault, and broader secrets-management integration
   ecosystem.
7. QxVault is hardened by default and includes automation for enforcing
   security practices such as certificate issuance and rotation.
8. QxVault simplifies HA cluster deployment and management, including
   zero-downtime upgrades.
9. QxVault reduces the need for platform operators to touch plaintext
   cryptographic keys, certificates, raw secrets, or HSM APIs directly.

The paper does not define a Clear-specific signing protocol. It also does not
provide exact endpoint-level detail for every operation Clear may eventually
need. Clear should treat the paper as evidence of a promising deployment and
custody substrate, not as a complete integration specification.

## Why this matters to Clear

Clear's security posture depends on more than web application hardening. A
Clear mint signs blinded outputs, maintains spent-proof state, and enforces
issuer and treasurer policy around supply-changing actions. If keyset secrets
or mint service keys are mishandled, a mint can lose the integrity of the
instrument it issues.

The strongest alignment with QxVault is operational:

- QxVault addresses secrets sprawl, while Clear wants to eliminate raw mint
  secrets from environment variables, compose files, and operator shells.
- QxVault offers OpenBao-compatible APIs, while Clear already has an
  OpenBao-oriented custody design direction.
- QxVault integrates an HSM, while Clear ultimately wants signing operations
  behind a boundary that never returns keyset secrets to the application
  process.
- QxVault emphasizes HA secrets infrastructure, while Clear mint availability
  depends on reliable access to custody operations.
- QxVault reduces HSM operational expertise requirements, while many Clear
  issuers may be communities, companies, agencies, or service operators that
  need strong custody without building a cryptography team.

The result is a natural deployment pattern:

```text
Clear policy and mint service
  -> OpenBao-compatible custody API
       -> QxVault appliance
            -> integrated HSM
```

QxVault should not decide whether a CMU may be issued or redeemed. Clear's
policy layer decides that. QxVault should protect the secrets and perform
bounded cryptographic operations after Clear has verified authority, policy,
grant limits, lifecycle state, and replay-prevention rules.

## Clear secret classes and QxVault relevance

Clear has multiple secret classes with different meanings. QxVault should not
collapse them into a single generic secret.

| Clear material | Why it matters | QxVault relevance |
| --- | --- | --- |
| Per-CMU keyset secret | Derives the Cashu denomination keys for one exact `cmu-<keyset-id>` | Highest priority; protect with QxVault Transit first, then move toward HSM-backed signing |
| Key-encryption material | Wraps keyset secrets at rest | Replace local key-encryption environment variables with QxVault-managed encryption |
| Mint service identity key | Signs service events, receipts, and possibly commissioning evidence | Move to QxVault-backed signing where compatible APIs support it |
| Operator credential | Gives privileged access to local operator surfaces | Replace or reduce with short-lived scoped credentials and private operator networks |
| Database credential | Protects the ledger, spent-proof state, and audit records | Use dynamic short-lived credentials where QxVault integrations support the database |
| Transport certificates | Protect Clear-to-QxVault and cluster communication | Use QxVault certificate lifecycle automation where available |
| Treasurer private key | Authorizes CMU operations under issuer policy | Keep outside the mint; QxVault should not centralize treasurer authority unless a treasurer independently chooses it |

The most important distinction is that the treasurer private key is authority
material, while a CMU keyset secret is operational mint custody material. A
treasurer authorizes a CMU or supply action. The treasurer does not
automatically receive the keyset secret.

## Per-CMU custody is the central design issue

Each treasurer-authorized CMU should have its own keyset secret and custody
record.

```text
treasurer signs keyset/create authorization
  -> Clear verifies grant, scope, policy, nonce, and limits
  -> one fresh keyset secret is created for that CMU
  -> public keys define cmu-<keyset-id>
  -> custody metadata binds that secret to the exact CMU
```

This gives Clear a clean boundary:

- one CMU;
- one keyset secret;
- one custody envelope or signer key identity;
- one lifecycle state;
- one treasurer policy context; and
- one spent-proof and supply accounting boundary.

Near term, Clear can generate the keyset secret internally and immediately send
it to QxVault Transit for encryption. The database stores only the wrapped
envelope:

```json
{
  "kind": "qxvault-transit-v1",
  "cmu": "cmu-<keyset-id>",
  "keyset_id": "<keyset-id>",
  "treasurer_npub": "npub...",
  "key": "clear-keyset-wrap",
  "ciphertext": "bao:v1:..."
}
```

That is better than local plaintext or locally wrapped key material, but it is
not the final boundary. If a compromised Clear process can call decrypt, it can
recover the keyset secret during runtime.

The target state is operation-based custody:

```text
Clear verifies treasury policy and supply state
  -> Clear submits blinded outputs and authorization evidence
  -> QxVault-backed signer verifies request context
  -> signer signs blinded outputs for the exact CMU
  -> raw keyset secret never returns to Clear
```

That target may require a Clear-specific signer or plugin near the QxVault/HSM
boundary. The paper's OpenBao compatibility is enough to justify a first
Transit-based integration, but Clear must verify whether the available API can
support the later signing boundary directly.

## Integration model

Clear should integrate QxVault through a custody provider abstraction:

```text
Clear policy layer
  -> KeyCustodyProvider
       -> LocalKeyProvider
       -> OpenBaoTransitProvider
       -> QxVaultTransitProvider
       -> FuturePolicySignerProvider
```

This keeps QxVault from leaking into Clear's public protocol. Wallets,
treasurers, and holders should not need to know whether the mint uses local
development secrets, OpenBao, QxVault, or another custody provider. They should
see the same CMU identity, Mint Note behavior, proof validation, and redemption
policy.

The provider boundary should support:

- encrypting a per-CMU keyset secret;
- decrypting a per-CMU keyset secret only in interim designs;
- rewrapping custody envelopes;
- returning public identity material;
- signing mint service events;
- issuing or renewing short-lived runtime credentials; and
- eventually signing blinded outputs without returning raw key material.

## Deployment architecture

A production QxVault-backed Clear deployment should separate the public mint
surface from the private custody surface:

```text
holders and wallets
  -> Clear public mint API
       -> Clear policy and proof-state layer
            -> private QxVault API
                 -> integrated HSM
```

Operator and treasury paths should remain distinct:

```text
treasurer wallet
  -> signed authorization
  -> Clear treasury endpoint
  -> policy verification
  -> QxVault custody operation
```

QxVault should not be exposed as part of the public mint route. It is internal
critical infrastructure. If QxVault is unavailable, Clear should fail closed
for operations requiring custody access, including issuance, signing, rewrap,
and any redemption path that requires keyset operations. Read-only public
metadata may remain available.

## Where QxVault improves Clear

QxVault can improve Clear along several dimensions.

### Reduced raw secret exposure

Clear deployments can move away from raw secrets in environment variables,
developer machines, compose files, and operator shells. This is especially
important for keyset wrapping material and mint service identity keys.

### Stronger production posture

The paper emphasizes hardened defaults, certificate automation, and guided
handling of core credentials. That maps directly to Clear deployments where
operators need a secure mint without hand-building an HSM-backed secrets
cluster.

### Lower operational barrier

Clear may be deployed by organizations that understand their treasury policy
but do not have an HSM operations team. A QxVault-style appliance could let
those organizations operate stronger custody without becoming cryptographic
infrastructure specialists.

### Better compliance story

The paper's FIPS 140-3 Level 3 HSM claim may matter for public-sector,
financial, regulated, or state-recognized deployments. Clear should not treat
FIPS as a magic compliance answer, but HSM-backed custody can be a credible
part of an assurance package.

### High availability for custody operations

Clear's mint service depends on custody. If custody is down, supply-changing
operations should stop. QxVault's HA emphasis is therefore relevant to Clear's
production availability.

## What QxVault does not solve by itself

QxVault is not a complete Clear security model.

It does not by itself:

- decide who is authorized to mint a CMU;
- define issuer redemption policy;
- distinguish acceptance from transferability;
- prevent a valid treasurer key from authorizing a bad business decision;
- maintain Clear's spent-proof state;
- solve split-brain mint clustering;
- make bearer-proof handling safe inside wallets;
- eliminate network, timing, or redemption metadata leakage;
- verify that a CMU is legally or commercially appropriate; or
- guarantee that a Clear-specific Cashu signing operation is available through
  the stock OpenBao-compatible API.

Clear must keep its own policy checks, supply accounting, proof validation,
spent-state controls, audit model, and wallet safety rules.

## Implementation roadmap

### Phase 1: QxVault Transit wrapping

Add `QxVaultTransitProvider` behind Clear's custody abstraction. New per-CMU
random keyset secrets are wrapped through QxVault Transit and stored as
`qxvault-transit-v1` envelopes.

Acceptance criteria:

- local provider behavior remains available for development;
- QxVault provider stores no token or plaintext key material in the database;
- every envelope records exact CMU and keyset identity;
- decrypt is available only to policy-approved code paths; and
- logs redact ciphertext plaintexts, tokens, and key material.

### Phase 2: rewrap existing CMUs

Add a root-only rewrap command:

```text
clear-root cmu rewrap-secrets --from local-v1 --to qxvault-transit-v1
```

Rewrapping must not change public keys, keyset IDs, CMUs, outstanding Mint
Notes, supply records, or spent-proof state.

### Phase 3: service identity signing

Move the mint service identity from raw `nsec` custody into QxVault-backed
signing if the compatible API supports the required signature operations.

### Phase 4: dynamic infrastructure credentials

Use QxVault for database credentials, internal certificates, backup job
credentials, and operator maintenance access. This reduces long-lived
deployment secrets around Clear.

### Phase 5: policy-aware Cashu signer

Design or integrate a Clear-specific signer that can use QxVault/HSM-backed
key material without returning per-CMU keyset secrets. This is the strongest
production boundary, but it likely requires more than generic secret storage.

## Evaluation questions for QxVault

Before committing to a production integration, Clear should answer:

1. Which QxVault endpoints exactly match OpenBao Transit encrypt, decrypt,
   rewrap, key versioning, and signing?
2. Does QxVault support Ed25519 signing in a way compatible with Clear's mint
   service identity needs?
3. Can QxVault generate per-CMU key material inside the HSM boundary and return
   only public descriptors?
4. Can QxVault or an external plugin perform Cashu denomination signing without
   releasing raw keyset secrets?
5. What workload identity mechanism should a containerized Clear deployment
   use to authenticate to QxVault?
6. How are QxVault audit records exported, retained, and correlated with Clear
   issuance and redemption records?
7. How should Clear coordinate database backups with QxVault snapshots?
8. What happens to Clear issuance, swap, redemption, and retirement if QxVault
   is unreachable?
9. What latency does QxVault add to signing-heavy operations?
10. How does QxVault cluster recovery avoid split-brain signing for the same
    active CMU?

## Policy conclusion

QxVault is strategically interesting for Clear because it helps turn Clear from
"software with important secrets" into "minting infrastructure with an
operation-based custody boundary." Its OpenBao-compatible API makes it a
practical near-term fit for key wrapping and secret lifecycle management. Its
integrated HSM and HA deployment model make it relevant for production and
regulated environments.

The strongest Clear architecture still requires Clear-specific policy
enforcement. QxVault can protect keys and perform cryptographic operations, but
Clear must decide when an operation is authorized, which CMU it belongs to, what
issuer policy governs it, and how spent-proof state is preserved.

The correct framing is therefore:

```text
Clear governs minting authority and bearer-note state.
QxVault hardens custody and cryptographic operations.
```

