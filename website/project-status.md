---
title: Project Status
description: Current implementation status and next milestones for Clear.
---

# Project Status

Clear is developer-stage software. The current implementation is a focused
protocol experiment, not a production mint.

## Implemented

- deterministic denomination key derivation;
- keyset-bound protocol-unit derivation using legacy identifier syntax;
- database enforcement of mint identity;
- Cashu v2 keyset identity;
- public key and keyset discovery;
- treasurer-authorized `clear` mint quotes;
- blinded issuance with idempotent request handling;
- atomic same-currency swaps;
- proof signature validation and spent-state checks;
- protected proof retirement;
- SQLite supply and audit accounting;
- FastAPI, Poetry CLI, tests, and documentation.

## Next

The first release is intentionally limited to one operator running one
authoritative Clear deployment with several isolated keysets and CMUs. See the
[Release Roadmap](release-roadmap.md) for the boundary and acceptance criteria.

- migrate the protocol unit from superseded prototype unit syntax to the canonical
  `cmu-<keyset-id>` identifier across code, APIs, databases, tests, and fixtures;
- update user-facing and protocol-facing code to distinguish Mint Notes from
  implementation-level Cashu proofs;
- replace the global operator token with signed, currency-scoped treasurer
  authorizations;
- add versioned, root-signed Nostr policy events stored as JSON and activated
  only through local installation and a deliberate mint restart;
- keep complete-policy relay publication optional and separate from public
  policy commitments and service records;
- provide a guided, proof-of-possession-checked treasurer `npub` replacement
  command;
- give each currency a distinct mint-service `npub` and home-relay set;
- add the separately installable `clear-treasury` authorization and token CLI;
- add operator-approved portable keyset enrollment for explicitly appointed
  keyset custodians or delegated treasurer-signers;
- define proof-of-control, activation, suspension, and audit records for an
  enrolled keyset;
- separate durable governance-root identity from operational keysets without
  treating their distinct CMUs as interchangeable;
- introduce isolated multi-currency routing and ledgers;
- implement the NUT-18 CMU payment-request profile and shared wallet codecs;
- test interoperability with Acorn and other custom-unit-capable wallets;
- define a signed currency policy record;
- add operator approval scopes and multi-party authorization;
- design backup and rollback detection;
- evaluate TROPIC01 or another hardware-backed signer boundary;
- publish auditable issuance and retirement summaries; and
- design keyset migration without implying currency equivalence.

Cross-currency exchange is intentionally deferred.

## After the first release

- define signed mint-cluster membership selected under treasury policy and
  approved by participating mint operators;
- support several mint instances for one CMU only after introducing strongly
  consistent issuance, authorization, and spent-proof state;
- design an authenticated mint-to-mint nullifier reservation, commit, and
  catch-up protocol; and
- design partition handling and cluster recovery without weakening the live
  double-spend boundary.

See the
[multi-currency treasurer authorization design](https://github.com/trbouma/clear/blob/main/docs/MULTI-CURRENCY-TREASURER-AUTHORIZATION-DESIGN.md)
for the proposed authority, policy, and migration model.
