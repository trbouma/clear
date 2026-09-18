---
title: QxVault and Clear
description: Why hardware-backed OpenBao-compatible custody matters for Clear mint deployments.
---

# QxVault and Clear

Clear is digital minting infrastructure. That means a Clear deployment is not
only a web service. It is also custody infrastructure for issuer-defined,
redeemable bearer instruments.

The QxVault whitepaper matters because it addresses a practical problem Clear
will face in production: how should a mint protect the secrets that let it
issue, redeem, and account for private Mint Notes?

QxVault is presented as a hardened secrets management appliance with
OpenBao-compatible application programming interfaces (APIs), an integrated
Hardware Security Module (HSM), high availability clustering, automated
credential management, and reduced need for HSM expertise. Those capabilities
map directly to Clear's production custody problem.

## Clear needs stronger custody than environment variables

A Clear mint has several sensitive secret classes:

- per-Clear Mint Unit (CMU) keyset secrets;
- mint service identity keys;
- operator credentials;
- database credentials;
- transport certificates; and
- recovery and audit material around issuance, redemption, and spent-proof
  state.

In early development, some of these secrets can live in local configuration.
That is not the right production boundary. A compromised runtime with access to
raw key material could compromise the mint.

QxVault points toward a better model:

```text
Clear policy layer
  -> custody operation
       -> QxVault private API
            -> integrated HSM
```

The application should ask for narrow operations, not casually hold every raw
secret it depends on.

## The most important secret is per-CMU

Each treasurer-authorized CMU should have its own keyset secret. That secret is
what gives the mint operational power to sign valid Mint Notes for the exact
`cmu-<keyset-id>`.

The treasurer authorizes creation or supply changes, but the treasurer does
not automatically receive the keyset secret. The keyset secret belongs to the
operational custody boundary for that CMU.

```text
treasurer authorizes one CMU
  -> Clear verifies policy, scope, nonce, and limits
  -> one fresh keyset secret is created or requested
  -> the public keyset defines cmu-<keyset-id>
  -> future signing uses custody operations for that CMU
```

This matters because one Clear mint may serve many treasurers and many CMUs.
Custody must not become one undifferentiated master secret. QxVault should help
Clear keep each CMU's key material separately wrapped, audited, rotated, or
eventually signed inside an HSM-backed boundary.

## Near-term use: wrap CMU keyset secrets

The first useful integration is straightforward. Clear can generate a random
keyset secret for a CMU and immediately ask QxVault to encrypt it. Clear stores
only a custody envelope in its database.

```text
Clear creates per-CMU keyset secret
  -> QxVault Transit encrypts it
  -> Clear stores encrypted envelope and CMU metadata
```

This removes durable wrapping material from the Clear environment and gives
operators a stronger place to rotate, audit, and control access to key
material.

It is not the final state. If Clear can ask QxVault to decrypt the secret, a
compromised Clear process may still be dangerous. But it is a practical first
step away from raw secrets in configuration.

## Target use: sign without releasing key material

The stronger target is operation-based signing. Instead of returning a keyset
secret to Clear, QxVault or a Clear-specific signer backed by QxVault would
perform the signing operation after Clear has verified policy.

```text
Clear verifies treasurer authority and supply state
  -> Clear submits blinded outputs and evidence
  -> signer checks CMU, keyset, policy, and operation id
  -> signer signs blinded outputs
  -> raw keyset secret never returns to Clear
```

This is the right long-term posture for production minting. Clear remains
responsible for treasury policy and spent-proof state. QxVault strengthens the
custody and cryptographic operation boundary.

## QxVault does not replace Clear governance

QxVault can protect secrets. It does not decide what a CMU means.

Clear still needs to answer:

- Who may authorize issuance?
- What does the issuer promise on redemption?
- Which CMU is being signed?
- Which treasurer policy applies?
- Has this authorization already been consumed?
- Has this proof already been spent?
- What happens if a CMU is suspended, retired, or moved to redemption-only?

Those are Clear policy and mint-state questions. QxVault can make the custody
boundary stronger, but it cannot replace the institutional logic of a mint.

## Why this matters for production Clear

QxVault is important because Clear is attracting use cases where custody will
matter: community units, corporate credits, compute credits, public-purpose
programs, delegated mints, and organizations representing state interests.

Those issuers may not want to build their own HSM-backed secrets platform.
They may still need strong custody, high availability, auditability, and a
credible story about who can use key material.

QxVault's OpenBao-compatible API is especially useful because it lets Clear
integrate through a standard custody abstraction rather than inventing a
one-off hardware integration. The public Clear protocol does not need to change
when an operator moves from local development secrets to QxVault-backed
custody.

## The policy takeaway

Clear and QxVault solve different problems:

```text
Clear governs minting authority, CMU identity, Mint Notes, and spent-proof state.
QxVault hardens secret custody, credential lifecycle, and cryptographic operations.
```

That combination is powerful. It lets Clear preserve its role as
issuer-defined digital minting infrastructure while giving production operators
a stronger path for protecting the secrets that make a mint trustworthy.

For the detailed technical analysis, see
[QxVault and Clear Analysis](https://github.com/trbouma/clear/blob/main/docs/QXVAULT-CLEAR-ANALYSIS.md).
