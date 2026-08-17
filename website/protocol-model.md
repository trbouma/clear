---
title: Protocol Model
description: How Clear issues, transfers, redeems, and retires Mint Notes without Lightning.
---

# Protocol Model

!!! note "Prototype protocol"
    This page describes the endpoints implemented in the first Clear
    prototype. The planned governance layer replaces the operator token with
    signed treasurer instructions governed by a root-signed policy. See
    [How Clear Is Governed](governance.md).

Clear preserves the central Cashu model:

- blinded Diffie-Hellman key exchange over secp256k1;
- denomination-specific keys grouped into a keyset;
- blinded outputs and blind signatures;
- bearer proofs containing a secret and unblinded signature;
- atomic proof swaps;
- spent-secret tracking; and
- proof-state checks.

In product and protocol language, the resulting bearer instruments are **Mint
Notes** denominated in a **Clear Mint Unit (CMU)**. In implementation language, each
spendable Mint Note is represented by a Cashu proof. The distinction keeps the
instrument understandable without renaming Cashu data structures.

## Clear issuance method

Cashu NUT-04 provides a general quote flow and allows method-specific
settlement mechanisms. Clear introduces the experimental method name `clear`:

1. A wallet requests a `clear` mint quote for one exact
   `cmu-<keyset-id>`.
2. The quote begins with no authorized amount.
3. The prototype authorizes the quote through its protected operator boundary.
4. The wallet submits blinded outputs up to the authorized amount.
5. Clear returns blind signatures and records issued supply.

The prototype derives its initial keyset secret locally and never accepts it
over the HTTP API. New keysets will instead be generated from independent
random secrets inside the mint after a signed, bounded treasurer
authorization. The mint encrypts those secrets at rest and never returns them
through a routine API.

The prototype uses a separate operator token for routine actions. The intended
model instead requires a signed authorization from a treasurer named in the
active policy. The operational signer remains in mint custody and releases
signatures only after authorization and ledger checks succeed.

The Clear Mint Unit is not operator-selected. The target protocol identifier is
formed from the exact NUT-02 keyset ID:

```text
cmu-<keyset-id>
```

Each new keyset creates a new CMU. A currency root may authorize several
keysets, but it does not make their Mint Notes automatically interchangeable.
A configured friendly name remains presentation metadata.

!!! note "Canonical identifier implemented"
    The current service exposes `cmu-<keyset-id>` across API responses,
    database identity, and circulating tokens.

## Clear redemption and retirement

Redemption and retirement are intentionally distinct from Cashu
melt-to-payment behavior:

1. The organization receives Mint Notes under its own policy.
2. The treasurer submits their Cashu proofs to the protected retirement
   endpoint.
3. Clear validates the notes and confirms they are unspent.
4. Their secrets are atomically marked spent, completing protocol redemption.
5. The amount is recorded as retired supply.

## Compatibility boundary

Mint Notes use normal Cashu proof structures and swaps. However, `clear` is
not currently a published Cashu NUT, and many wallets assume familiar units or
Lightning settlement. Compatible wallets must support keyset-bound CMU strings
and the Clear quote workflow.

The implementation follows the public
[Cashu NUTs](https://github.com/cashubtc/nuts) and takes architectural guidance
from the Python [Nutshell](https://github.com/cashubtc/nutshell) reference
implementation without presenting Clear as a drop-in replacement.
