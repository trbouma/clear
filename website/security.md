---
title: Security
description: Clear's current trust and security boundary.
---

# Security

Clear is experimental software and has not been audited.

!!! note "Current implementation and intended model"
    The current prototype derives one keyset from a master secret and uses a
    separate operator token. New keysets will use independent random secrets,
    authorized by treasurers and encrypted in mint custody, as part of the
    root authority, mint operator, treasurer, mint service, and operational
    signer separation described in
    [How Clear Is Governed](governance.md). That model is not fully implemented
    yet.

## Keyset control

The master secret controls every denomination key in the configured keyset.
Anyone who obtains it can create valid Mint Notes outside the ledger and
therefore inflate the corresponding CMU without detection by this service.
Protecting it is the issuer's highest-priority responsibility.

A treasurer authorizes creation of a new keyset but does not receive its random
secret. The target mint encrypts each independently generated keyset secret at
rest. Compromise or migration of one keyset must not expose another keyset or
the mint's key-encryption key. Enforceable separation from a compromised mint
process eventually requires a policy-enforcing HSM or remote signer.

Treasurer authority and keyset custody are separate responsibilities. The
treasurer `nsec` authorizes bounded actions for a CMU. The mint operator is
responsible for the keyset secret, the key-encryption material, backups, and
any runtime environment that can decrypt or use the signing material. Rotating a
treasurer `npub` changes who may authorize future actions; changing a keyset
secret creates a different keyset and therefore a different CMU.

The current service derives keys locally and never accepts the master secret
over HTTP. Routine issuance and retirement use a separate operator token so
that keyset material does not become an API credential. The target service
also never returns a random keyset secret through routine APIs.

The target protocol unit is `cmu-<keyset-id>`, using the exact NUT-02 keyset ID.
The human-readable currency name and abbreviation `CMU` are not trusted as
identifiers. Keyset rotation creates a new CMU rather than silently continuing
the old balance.

## Operator control

A local process with the operator token can authorize supply and redeem and
retire valid Mint Notes. Operator endpoints enforce a loopback client boundary;
a valid token presented remotely is rejected. Run `clear-root` inside the mint
container or trusted local mint environment, rotate the token after suspected
exposure, and never place it in browser applications.

This token is a temporary prototype mechanism. In the intended model, the mint
operator has no inherent issuance authority. Root-signed policy events appoint
treasurers, and signed treasurer instructions authorize individual supply
changes.

## Commissioning control

Signed treasurer authority is accepted only after root commissioning succeeds
and the root explicitly enables treasury operations. The verification record
is bound to critical software, schema, configuration, key storage, and audit
state. Changes that invalidate those assumptions close the treasury gate.

Root verification uses the same treasury action layer as treasurer requests.
A privileged shortcut would not prove that the delegated workflow is safe to
operate. Commissioning adds operational evidence; it does not replace an
independent audit or guarantee the issuer's real-world promises.

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
- no durable root commissioning record or treasury enable gate;
- no proof-of-liabilities publication;
- no operator roles or multi-party approval;
- no rate limiting; and
- no cross-currency swaps.
