---
title: Project Status
description: Current implementation status and next milestones for Clear.
---

# Project Status

Clear is developer-stage software. The current implementation is a focused
protocol experiment, not a production mint.

## Implemented

- deterministic denomination key derivation;
- keyset-bound protocol-unit derivation;
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
- separate durable currency-root identity from replaceable operational
  keysets;
- introduce isolated multi-currency routing and ledgers;
- test interoperability with Acorn and other custom-unit-capable wallets;
- define a signed currency policy record;
- add operator approval scopes and multi-party authorization;
- design backup and rollback detection;
- evaluate TROPIC01 or another hardware-backed signer boundary;
- publish auditable issuance and retirement summaries; and
- design keyset migration without implying currency equivalence.

Cross-currency exchange is intentionally deferred.

See the
[multi-currency treasurer authorization design](https://github.com/trbouma/clear/blob/main/docs/MULTI-CURRENCY-TREASURER-AUTHORIZATION-DESIGN.md)
for the proposed authority, policy, and migration model.
