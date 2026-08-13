---
title: Protocol Model
description: How Clear adapts Cashu issuance and retirement without Lightning.
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

## Clear issuance method

Cashu NUT-04 provides a general quote flow and allows method-specific
settlement mechanisms. Clear introduces the experimental method name `clear`:

1. A wallet requests a `clear` mint quote for a unique Clear unit.
2. The quote begins with no authorized amount.
3. The prototype authorizes the quote through its protected operator boundary.
4. The wallet submits blinded outputs up to the authorized amount.
5. Clear returns blind signatures and records issued supply.

The keyset secret never crosses the HTTP boundary. The prototype uses a
separate operator token for routine actions. The intended model instead
requires a signed authorization from a treasurer named in the active policy.

The prototype unit is not operator-selected. It is deterministically bound to
the keyset's public-key fingerprint. The intended multi-keyset model binds the
durable unit to the currency root and separately identifies each operational
keyset. A configured friendly name remains presentation metadata rather than
currency identity.

## Clear retirement

Retirement is intentionally distinct from Cashu melt-to-payment behavior:

1. The organization receives proofs under its own policy.
2. The treasurer submits them to the protected retirement endpoint.
3. Clear validates the signatures and confirms they are unspent.
4. Their secrets are atomically marked spent.
5. The amount is recorded as retired supply.

## Compatibility boundary

Issued proofs use normal Cashu proof structures and swaps. However, `clear` is
not currently a published Cashu NUT, and many wallets assume familiar units or
Lightning settlement. Compatible wallets must support custom unit strings and
the Clear quote workflow.

The implementation follows the public
[Cashu NUTs](https://github.com/cashubtc/nuts) and takes architectural guidance
from the Python [Nutshell](https://github.com/cashubtc/nutshell) reference
implementation without presenting Clear as a drop-in replacement.
