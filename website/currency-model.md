---
title: Clear Mint Unit and Currency Model
description: The keyset-bound Clear Mint Unit, supply, and policy model for Clear Mint Notes.
---

# Clear Mint Unit and Currency Model

## One keyset, one Clear Mint Unit

Each Clear keyset defines a distinct Clear Mint Unit. The canonical protocol unit is:

```text
cmu-<keyset-id>
```

For example:

```text
cmu-00a1b2c3d4e5f6
```

The visible abbreviation **CMU**, pronounced as the letters “C-M-U,” is not sufficient
identity. Applications must retain the complete CMU and the authenticated
issuer or policy domain that recognizes it. A mint endpoint is a service route:
one logical mint may expose a mint cluster of authorized endpoints. Notes from
different issuers or CMUs are separate bearer instruments and must never be
added or spent together merely because their numeric amounts match.

Several Clear instances may serve one CMU only as a configured mint cluster
with strongly consistent issuance, authorization, and spent-note state.
Independent instances require independent keysets and therefore distinct CMUs.

## Policy domain and keysets

A Clear program may have a durable currency root that governs policy,
treasurers, mint-service identities, and authorized keysets. That governance
domain does not create a root-bound protocol unit. Each authorized keyset still
defines its own CMU.

A policy domain may contain:

- a currency-root fingerprint;
- a human-readable program or currency name;
- a root-signed governance policy;
- authorized treasurer public keys and approval rules;
- one or more currency-specific mint-service identities;
- one or more authorized Cashu keysets and their distinct CMUs; and
- isolated issuance, redemption, retirement, and spent-proof accounting for
  each CMU.

The intended setup follows a fixed order:

1. Create a currency-root key offline or in protected hardware.
2. Derive the currency fingerprint from its public key.
3. Sign the first policy event, appointing treasurers and mint identities.
4. Authorize an operational Cashu keyset.
5. Derive the standard NUT-02 keyset ID for its denomination public keys.
6. Form the protocol unit as `cmu-<keyset-id>`.

Changing the friendly name does not change an existing CMU. Rotating an
operational keyset does: the new keyset defines a new CMU and a distinct
balance. The root authority may authorize an explicit exchange or migration,
but it cannot silently declare the notes equivalent.

!!! note "Canonical unit implemented"
    Clear derives and exposes the canonical `cmu-<keyset-id>` identifier
    through its API, database identity, and circulating tokens. Existing
    deployments remain bound to the keyset identity recorded when their
    database was created.

## Supply equation

Clear records a simple supply relationship:

```text
outstanding = Mint Notes issued - Mint Notes redeemed and retired
```

Swaps within one CMU do not change supply. They consume old Cashu proofs and
sign new blinded outputs of exactly the same total amount.

## Issuance policy

Clear provides a mechanism for authorization, not a universal issuance rule.
The root-signed policy determines which treasurers may act and whether several
approvals are required. A treasurer may rely on a budget, membership decision,
completed work, donation, inventory receipt, or another organizational event.
That rationale can be recorded as a memo, but the organization still defines
what its Mint Notes represent.

## Redemption and retirement

Redemption is the protocol action of returning a Mint Note to its issuing mint
for validation and consumption. Retirement is the Clear accounting outcome
when that redeemed note is permanently removed from circulation. Neither term
by itself promises cash, debt discharge, or delivery of a good. Those meanings
come from the issuer's policy.

## Future exchange

Clear does not initially swap across CMUs. A future exchange policy may quote a
rate and atomically redeem and retire notes from one CMU while issuing notes in
another, but it must never make separate balances appear naturally
interchangeable.
