---
title: Mint Notes and CMU
description: The canonical vocabulary for Clear mints, Mint Notes, denominations, and keyset-bound Clear Mint Units.
---

# Mint Notes and CMU

Clear distinguishes the issuer, the bearer instrument it issues, and the unit
used to denominate that instrument.

```text
Mint
└── operates a keyset
    └── defines cmu-<keyset-id>
        └── issues Mint Notes denominated in that CMU
```

## Mint

A **Mint** is a cryptographic issuer and redeemer of bearer instruments. It
operates cryptographic keysets, issues Mint Notes, validates returned notes,
and prevents the same note from being redeemed twice.

## Mint Note

A **Mint Note** is a cryptographically issued bearer instrument representing a
fixed denomination. It is issued by one mint keyset, transferable by the
protocol, and redeemable by the issuing mint.

Examples include:

- a 1 CMU Mint Note;
- a 64 CMU Mint Note; and
- a 1024 CMU Mint Note.

## Clear Mint Unit

A **Clear Mint Unit**, abbreviated **CMU** and pronounced as the letters
“C-M-U,” is Clear's concrete form of the generic mint-unit concept. It is
defined by a mint keyset, and its name reflects Clear's role in issuing,
redeeming, and clearing Mint Notes under an explicit policy. Its canonical
protocol identifier is:

```text
cmu-<keyset-id>
```

For example:

```text
cmu-00a1b2c3d4e5f6
```

The complete CMU and authenticated issuer policy identify the balance. A mint
endpoint is a service route, and one logical mint may expose a **mint cluster**
of authorized instances. Notes from different logical mints or keysets are not
interchangeable merely because both display `CMU`.

## Portable keysets and several instances

A treasurer may be separately appointed as the custodian or delegated signer
for a keyset. With mint-operator approval, that keyset can be enrolled in an
existing Clear deployment. Possession of the keyset secret is cryptographic
issuance power, so the role must be explicit and the secret strongly
protected.

The same keyset can be served through a mint cluster, allowing Mint Notes in
one CMU to be issued or redeemed at different endpoints. The active policy
identifies which member mints must be checked for double-spend state. Cluster
members need synchronous shared state or a reserve-and-commit protocol;
periodic synchronization alone leaves a race in which two mints could accept
the same note. Independent instances must use different keysets and CMUs.

## Keyset rotation creates a new CMU

A new keyset defines a new Clear Mint Unit. The old and new notes remain separate
unless the issuer offers an explicit migration or exchange:

```text
cmu-<old-keyset-id> != cmu-<new-keyset-id>
```

A durable currency root may authorize both keysets, but it does not silently
make their notes equivalent. Wallets must keep the balances distinct and show
the terms of any conversion.

## Mint Notes and Cashu proofs

*Mint Note* is the product and protocol term for the bearer instrument. *Cashu
proof* remains the technical term for the structure containing its amount,
keyset ID, secret, and unblinded signature. A Mint Note issued using Chaumian
blind signatures may also be described as a **Chaumian Note**.

## Redemption and retirement

Redemption means returning a Mint Note to its issuing mint for validation and
consumption. Clear may record that redemption as retirement, permanently
removing the note from circulation. Retirement does not by itself promise a
Bitcoin, fiat, goods, or service payout; the issuer’s policy defines any
external consequence.

!!! note "Canonical unit"
    Clear now exposes `cmu-<keyset-id>` as the protocol contract across its
    API, database identity, and circulating tokens.

The complete normative vocabulary is maintained in
[the repository specification](https://github.com/trbouma/clear/blob/main/docs/MINT-NOTES-VOCABULARY.md).
