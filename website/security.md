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
Anyone who obtains it can create valid Mint Notes outside the ledger and
therefore inflate the corresponding CMU without detection by this service.
Protecting it is the issuer's highest-priority responsibility.

A treasurer may deliberately be appointed as a keyset custodian or delegated
signer. In that case, the treasurer can enroll the keyset with an operator-
approved mint instance and issue through the approved workflow. Operator
approval governs service recognition and accounting, but it cannot
cryptographically restrain someone holding the raw secret. Enforceable
two-party issuance requires a policy-enforcing HSM or remote signer.

The service derives keys locally and never accepts the master secret over HTTP.
Routine issuance and retirement use a separate operator token so that the
keyset secret does not become an API credential.

The target protocol unit is `cmu-<keyset-id>`, using the exact NUT-02 keyset ID.
The human-readable currency name and abbreviation `CMU` are not trusted as
identifiers. Keyset rotation creates a new CMU rather than silently continuing
the old balance.

## Operator control

Anyone with the operator token can authorize supply and redeem and retire valid
Mint Notes.
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

The same keyset may be served by a mint cluster only when its members share or
synchronously coordinate issuance, authorization-consumption, and spent-proof
state. Independent databases using the same keyset can accept the same proof
more than once. Eventual replication alone is not an adequate double-spend
boundary. A mint must fail closed when the members required by the active
cluster policy cannot participate in the reservation decision.

## Policy control

Cryptographic validity does not establish that an issuer followed its budget,
delivered promised goods, or will recognize a Mint Note later. Applications
should show the issuing mint, complete CMU, and applicable policy prominently.

## Current limitations

- no HSM or remote-signer integration;
- no signed policy documents;
- no key rotation or migration workflow;
- no proof-of-liabilities publication;
- no operator roles or multi-party approval;
- no rate limiting; and
- no cross-currency swaps.
