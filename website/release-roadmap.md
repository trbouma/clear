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

The operator can approve and enroll a keyset created by a treasurer or keyset
custodian. Once activated, Clear advertises that keyset, records its issuance,
and accepts responsibility for its Mint Notes. Keyset secrets are installed
through a protected local path, never through the public API.

Enrollment must happen before issuance. Clear does not retrospectively adopt
unrecorded notes merely because they validate under a newly imported keyset.

Each keyset remains its own CMU. Quotes, issuance, swaps, spent-note state,
redemption, retirement, and supply accounting are isolated. Clear does not
combine the balances simply because they share an operator or friendly name.

## What must work

- standard NUT-02 keyset IDs and `cmu-<keyset-id>` units;
- discovery and routing for several active keysets;
- operator-approved local keyset enrollment;
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

!!! note "Release posture"
    The first release remains experimental and unaudited. Its purpose is to
    establish a clean multi-keyset protocol and operational foundation before
    distributed issuance is attempted.

The detailed engineering checklist is maintained in the
[first-release scope](https://github.com/trbouma/clear/blob/main/docs/FIRST-RELEASE-SCOPE.md).
