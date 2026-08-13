---
title: Security
description: Clear's current trust and security boundary.
---

# Security

Clear is experimental software and has not been audited.

!!! note "Current implementation and intended model"
    The current prototype uses one master secret and a separate operator token.
    Clear is moving toward the root authority, mint operator, treasurer, mint
    service, and operational signer separation described in
    [How Clear Is Governed](governance.md). That model is not fully implemented
    yet.

## Keyset control

The master secret controls every denomination key in the configured keyset.
Anyone who obtains it can create valid proofs outside the ledger and therefore
inflate the currency without detection by this service. Protecting it is the
issuer's highest-priority responsibility.

The service derives keys locally and never accepts the master secret over HTTP.
Routine issuance and retirement use a separate operator token so that the
keyset secret does not become an API credential.

The protocol unit is derived from a fingerprint of the resulting public keys.
The human-readable currency name is not trusted as an identifier and can be
changed without changing the proofs.

## Operator control

Anyone with the operator token can authorize supply and retire valid proofs.
Use TLS, restrict the operator endpoints at the network boundary, rotate the
token after suspected exposure, and avoid placing it in browser applications.

This token is a temporary prototype mechanism. In the intended model, the mint
operator has no inherent issuance authority. Root-signed policy events appoint
treasurers, and signed treasurer instructions authorize individual supply
changes.

## Database control

The SQLite database contains quote state, spent-proof nullifiers, and the
supply audit log. Loss or rollback can permit double spending or make supply
reporting incorrect. Backups must preserve transaction order and rollback
protection.

## Policy control

Cryptographic validity does not establish that an issuer followed its budget,
delivered promised goods, or will recognize a point later. Applications should
show the issuer and currency identity prominently and link to the applicable
policy.

## Current limitations

- no HSM or remote-signer integration;
- no signed policy documents;
- no key rotation or migration workflow;
- no proof-of-liabilities publication;
- no operator roles or multi-party approval;
- no rate limiting; and
- no cross-currency swaps.
