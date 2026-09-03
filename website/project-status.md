---
title: Project Status
description: Current implementation status and next milestones for Clear.
---

# Project Status

Clear is developer-stage software. The current implementation is a focused
protocol experiment, not a production mint.

## Implemented

- deterministic denomination key derivation;
- canonical `cmu-<keyset-id>` protocol-unit derivation;
- database enforcement of mint identity;
- Cashu v2 keyset identity;
- public key and keyset discovery;
- treasurer-authorized `clear` mint quotes;
- blinded issuance with idempotent request handling;
- atomic same-currency swaps;
- proof signature validation and spent-state checks;
- protected proof retirement;
- SQLite supply and audit accounting;
- Docker deployment with separate public and privileged API URLs;
- wallet-facing currency and unit aliases;
- privileged `clear-root` bootstrap, issuance, treasury wallet, exact export,
  send, and retirement workflows;
- issued, retired, circulating, and local-wallet balance inspection;
- NIP-05 Clear capability discovery;
- NIP-59 kind `1059` delivery with inner kind `7379`;
- tested pending transfer interoperability with Acorn and Safebox Web;
- recipient acceptance into separate kind `7380` spendable proof state and
  kind `7381` append-only Clear history; and
- FastAPI, Poetry CLI, tests, and documentation.

## August 2026 transferable CMU milestone

Clear now demonstrates organization-issued CMUs moving from a mint-operated
treasury to a recipient wallet through a public mint, NIP-05 discovery, Nostr
relay delivery, Acorn receipt storage, and Safebox Web display.

This is the first end-to-end product-family proof that an organization-defined
unit can leave the issuer's application boundary as a private bearer transfer
and be accepted into a distinct spendable Clear Balance. It remains a lab
milestone: onward wallet spending and stronger crash recovery around acceptance
are not complete.

[Read the complete milestone](https://github.com/trbouma/clear/blob/main/docs/TRANSFERABLE-CMU-MILESTONE-2026-08-17.md){ .md-button .md-button--primary }

## September 2026 treasurer-authorized CMU milestone

Clear now demonstrates the first working multi-community treasury flow: a mint
operator authorizes a treasurer `npub`, the treasurer consumes a single-use
grant with their own `nsec`, the mint creates a separate random encrypted
keyset/CMU, and the treasurer can issue and send Mint Notes from a
treasurer-scoped wallet.

Safebox Web now displays friendly CMU labels from mint keyset metadata while
preserving the canonical identity of mint URL, CMU unit, and keyset ID. The
tested flow used **Food Share Credits** displayed in **shares**.

[Read the complete milestone](https://github.com/trbouma/clear/blob/main/docs/TREASURER-AUTHORIZED-CMU-MILESTONE-2026-09-03.md){ .md-button .md-button--primary }

## Next

The first release is intentionally limited to one operator running one
authoritative Clear deployment with several isolated keysets and CMUs. See the
[Release Roadmap](release-roadmap.md) for the boundary and acceptance criteria.

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
- add bounded `clear-root` treasurer grants for random keyset creation;
- add `clear-root verify`, a dedicated commissioning keyset, durable readiness
  records, and an explicit treasury enable gate;
- encrypt independent keyset secrets in mint custody;
- define creation authorization, activation, suspension, migration, and audit
  records for each keyset;
- separate durable governance-root identity from operational keysets without
  treating their distinct CMUs as interchangeable;
- introduce isolated multi-currency routing and ledgers;
- implement the NUT-18 CMU transfer-request profile and shared wallet codecs;
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
