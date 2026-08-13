---
title: Currency Model
description: The identity, supply, and policy model for a Clear currency.
---

# Currency Model

## One root, one currency

Each Clear currency has a durable root identity. Its root authority may
authorize new operational keysets without changing the currency held by its
users. A currency domain contains:

- a currency-root fingerprint;
- a protocol unit bound to that root, such as
  `pts.00a1b2c3d4e5f6`;
- a human-readable currency name;
- a root-signed governance policy;
- authorized treasurer public keys and approval rules;
- a currency-specific mint-service identity;
- one or more authorized Cashu keysets; and
- its own issuance, retirement, and spent-proof ledger.

The friendly name and display abbreviation `pts` are not sufficient identity.
Applications must group value by mint URL, protocol unit, and NUT-02 keyset ID,
then resolve that identity to a friendly name for presentation.

## Durable identity

Clear's intended currency setup follows a fixed order:

1. Create a currency-root key offline or in protected hardware.
2. Derive the currency fingerprint from its public key.
3. Form the protocol unit as `pts.<currency-root-fingerprint>`.
4. Sign the first policy event, appointing treasurers and mint identities.
5. Authorize an operational Cashu keyset for that currency.
6. Derive the standard NUT-02 keyset ID for its denomination public keys.

Changing the friendly name or rotating an operational keyset does not create a
new currency. Replacing the currency root does, unless a future explicit
migration protocol provides independently verifiable continuity.

!!! note "Current prototype"
    The current implementation binds the protocol unit directly to one
    operational keyset and uses an operator token. Moving to a durable currency
    root, signed policy events, and treasurer authorizations is the next
    architectural milestone.

## Supply equation

Clear records a simple supply relationship:

```text
outstanding = authorized issuance completed - proofs retired
```

Swaps do not change supply. They consume old proofs and sign new blinded
outputs of exactly the same total amount.

## Issuance policy

Clear provides a mechanism for authorization, not a universal issuance rule.
The root-signed policy determines which treasurers may act and whether several
approvals are required. A treasurer may rely on a budget, membership decision,
completed work, donation, inventory receipt, or another organizational event.
That rationale can be recorded as a memo, but the organization still defines
what its points mean.

## No implicit redemption promise

Retirement means that valid proofs were accepted back and permanently removed
from circulation. It does not itself mean cash redemption, debt discharge, or
delivery of a particular good. Those meanings come from the issuer's policy.

## Future exchange

Clear does not initially swap across currencies. A future exchange policy may
quote a rate and atomically retire one currency while issuing another, but it
must never make separate balances appear naturally interchangeable.
