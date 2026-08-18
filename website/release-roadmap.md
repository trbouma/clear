---
title: Release Roadmap
description: The focused boundary for Clear's first release and the mint-cluster work that follows.
---

# Release Roadmap

## First release: one operator, several CMUs

The first Clear release focuses on one operator running one authoritative mint
deployment that supports several independent keysets:

```text
Clear operator
├── Keyset A -> cmu-A -> ledger A
├── Keyset B -> cmu-B -> ledger B
└── Keyset C -> cmu-C -> ledger C
```

The operator can grant an authorized treasurer one use of `keyset:create`.
After verifying the treasurer's signed request, Clear generates an independent
random keyset secret inside the mint, encrypts it at rest, and records the
authorization. Once activated, Clear advertises that keyset, records its
issuance, and accepts responsibility for its Mint Notes.

Enrollment must happen before issuance. Clear does not retrospectively adopt
unrecorded notes merely because they validate under a newly imported keyset.

Each keyset remains its own CMU. Quotes, issuance, swaps, spent-note state,
redemption, retirement, and supply accounting are isolated. Clear does not
combine the balances simply because they share an operator or friendly name.

Before any treasurer is enabled, `clear-root` must commission the deployment.
It exercises the shared treasury action layer with a dedicated test keyset,
retires all test units, records durable readiness evidence, and then explicitly
opens the treasury gate. A critical configuration or storage change closes the
gate until verification succeeds again.

## What must work

- standard NUT-02 keyset IDs and `cmu-<keyset-id>` units;
- discovery and routing for several active keysets;
- treasurer-authorized random keyset creation and operator activation;
- root commissioning, durable readiness evidence, and an explicit treasury
  enable gate;
- one isolated authoritative ledger per CMU;
- complete issuance, swap, state-check, redemption, and retirement flows;
- NUT-18 transfer requests for one exact CMU and strict Clear endpoint;
- cross-CMU rejection and concurrent double-spend tests;
- restart, backup, and ledger-identity checks; and
- live wallet interoperability.

## Next release: mint clusters

A later release may allow several mint instances to serve the same CMU as a
mint cluster. That requires signed membership, synchronous nullifier
reservation, issuance coordination, partition handling, and state catch-up.

Mint clusters are deliberately deferred until the single-deployment,
multi-keyset model is boring and reliable. Periodic synchronization alone is
not enough to prevent two mint instances from accepting the same note.

## Future feature: protocol-enforced expiry

Expiry is outside the current Clear proof protocol. An issuer may publish an
expiry date as part of its program policy and apply that policy when deciding
whether or how to redeem returned Mint Notes. The date is not encoded in the
proof, does not alter signature validation, and does not automatically stop a
wallet from holding or transferring the note.

A future protocol-enforced design would need to:

- bind expiry or other lifecycle attributes cryptographically to the unit or
  proof;
- preserve those restrictions through blinded issuance and swaps;
- define mint behavior before and after expiry;
- distinguish expiry from holder redemption and administrative revocation;
- define wallet display, clock, grace-period, and offline behavior; and
- reconcile expired outstanding supply into retired accounting.

Clear will not add an unsigned expiry field to proofs or tokens. Editable
metadata would create the appearance of enforcement without changing what the
mint actually validates.

!!! note "Release posture"
    The first release remains experimental and unaudited. Its purpose is to
    establish a clean multi-keyset protocol and operational foundation before
    distributed issuance or protocol-enforced lifecycle conditions are
    attempted.

The detailed engineering checklist is maintained in the
[first-release scope](https://github.com/trbouma/clear/blob/main/docs/FIRST-RELEASE-SCOPE.md).
