# Mint Notes Vocabulary

## Status

This document defines the canonical terminology for Clear documentation and
the protocol contract. The current implementation exposes canonical
`cmu-<keyset-id>` identifiers across code, API, database identity, and tests.

## Overview

The protocol distinguishes the mint, the bearer instrument it issues, and the
unit in which that instrument is denominated.

```text
Mint
└── operates a keyset
    └── defines cmu-<keyset-id>
        └── issues Mint Notes denominated in that CMU
```

At the product-model level, a CMU belongs to the broader category of
**transferable units**. The hierarchy is:

```text
Transferable unit
└── Clear Mint Unit (CMU)
    └── represented by transferable Mint Notes
```

## Mint

A **Mint** is a cryptographic issuer and redeemer of bearer instruments.

Its protocol responsibilities are to:

- operate one or more cryptographic keysets;
- issue Mint Notes;
- validate and redeem Mint Notes it issued;
- prevent the same note from being redeemed twice; and
- expose the keyset and Clear Mint Unit needed by compatible wallets.

The mint does not, by cryptography alone, determine why notes are issued, what
an organization promises in return, or whether another party should accept
them. Those meanings come from issuer policy and recognition.

## Mint Note

A **Mint Note** is a cryptographically issued bearer instrument representing a
fixed denomination.

A Mint Note is:

- issued by exactly one mint keyset;
- denominated in exactly one Clear Mint Unit;
- transferable by the protocol; and
- redeemable only by its issuing mint.

Examples include a 1 CMU Mint Note, a 64 CMU Mint Note, and a 1024 CMU Mint
Note. Wallets may combine notes of the same CMU to express a total amount.

## Transferable unit

A **transferable unit** is a fungible unit whose control can move between
holders under an issuer's policy. It is the general category for units that can
circulate independently of an account maintained for each holder.

Transferability does not imply that a unit is cash, legal tender, universally
accepted, or redeemable for money. A transferable unit may instead represent a
guest pass, service credit, allowance, benefit, voucher, or another bounded
entitlement. Its issuer defines the equivalence domain, acceptance rules, and
redemption or retirement policy.

Clear Mint Unit is the exact Clear protocol term for a transferable unit
defined by a Clear keyset. Mint Notes are the unique bearer instruments that
represent quantities of that unit.

## Clear Mint Unit

A **Clear Mint Unit**, abbreviated **CMU** and pronounced as the letters
“C-M-U,” is Clear's concrete form of the generic mint-unit concept. It is the
unit of account defined by a mint keyset and expresses the denomination of
Mint Notes. The name also reflects Clear's role in issuing, redeeming, and
clearing those notes under an explicit policy.

The human-facing abbreviation is:

```text
CMU
```

The canonical protocol identifier is:

```text
cmu-<keyset-id>
```

For example:

```text
cmu-00a1b2c3d4e5f6
```

`<keyset-id>` is the exact NUT-02 keyset identifier. Applications must retain
the complete identifier rather than treating the visible abbreviation `CMU`
as sufficient identity.

## Identity, service endpoints, and interchangeability

A balance is identified by its complete CMU and the issuer or policy domain
that recognizes it. One endpoint or an authenticated **mint cluster** may
route to that logical mint:

```text
issuer or policy domain + cmu-<keyset-id> + mint or mint-cluster route
```

The endpoint is a service location, not necessarily a unique issuer. A mint
cluster is an explicitly configured set of Clear mint instances that serve the
same CMU as one logical mint and coordinate one authoritative issuance and
spent-note state.

Two notes are directly interchangeable only when they are recognized under the
same issuer policy and have the same canonical CMU identifier. Equal numeric
amounts do not make notes from different issuers or keysets equivalent.

A wallet may therefore hold:

```text
64 cmu-00a1b2c3d4e5f6
64 cmu-00998877665544
```

Those are separate balances and must never be added or spent together merely
because both are displayed as CMU.

## Keyset lifecycle

Keyset rotation creates a new keyset and therefore a new CMU:

```text
old keyset -> cmu-<old-keyset-id>
new keyset -> cmu-<new-keyset-id>
```

The notes are not automatically equivalent. An issuer may publish an explicit
migration or exchange policy that redeems notes from the old CMU and issues
notes in the new CMU. The wallet must present that conversion as an explicit
issuer action with visible terms, not as a silent continuation of the same
balance.

A durable currency root may govern policy and authorize keysets, but it does
not erase the boundary between the CMUs defined by those keysets.

## Portable keyset control

A keyset may be created outside a particular Clear instance and later enrolled
with a mint operator. A treasurer or signer custodian who controls the keyset
secret can prove control, provide its public keyset descriptor, and request
that an operator activate it under an approved policy. The operator decides
whether that Clear deployment will recognize, account for, and redeem Mint
Notes issued under the keyset.

Possession of the keyset secret is itself cryptographic issuance power. An
ordinary treasurer authorization key does not grant that power. Software cannot
prevent a holder of the raw keyset secret from signing notes outside the normal
workflow; operator approval governs admission to the mint's policy, accounting,
and redemption commitment. Enforceable two-party issuance therefore requires a
policy-enforcing signer or HSM that will sign only after both treasury
authorization and operator approval.

The same keyset may be made available through a mint cluster, allowing Mint
Notes in one CMU to be issued and redeemed at more than one endpoint. The
active policy must identify the cluster members whose double-spend state each
instance is required to consult.

This is safe only when cluster members coordinate a strongly consistent
issuance ledger, authorization-consumption state, and spent-proof set.
Periodically synchronizing spent proofs is valuable for recovery but is not,
by itself, a double-spend barrier: two instances could accept the same note
before the next synchronization. Redemption therefore requires a synchronous
single-writer or reserve-and-commit decision across the configured cluster.

Deploying the same keyset with independent databases would permit the same
note to be redeemed more than once and is prohibited. Independent mints must
use independent keysets and therefore distinct CMUs.

## Denominations

Mint Notes normally use fixed denominations supported by the keyset, such as:

```text
1, 2, 4, 8, 16, 32, 64, 128, ... CMU
```

For one CMU, the following holdings have the same total value:

```text
one 64 CMU note
two 32 CMU notes
sixteen 4 CMU notes
```

## Relationship to Cashu proofs

**Mint Note** is the protocol and product term for the bearer instrument.
**Cashu proof** remains the implementation term for the data structure that
encodes a spendable note, including its amount, keyset identifier, secret, and
unblinded signature.

When Chaumian blind signatures are used, **Chaumian Note** may be used as a
subtype:

```text
Note
└── Mint Note
    └── Chaumian Note
```

Documentation should use *Mint Note* when discussing what a holder owns or
transfers, and *proof* when discussing Cashu structures, signature validation,
nullifiers, API fields, or implementation behavior.

## Redemption, retirement, expiration, and revocation

**Redemption** is the protocol action in which a holder returns a Mint Note to
its issuing mint and the mint validates and consumes it.

**Retirement** is the generalized terminal lifecycle and accounting outcome in
which units are permanently removed from circulation. Redemption is the normal
holder-initiated path to retirement, but issuer policy may also call for
retirement after expiration, revocation, cancellation, reconciliation, or
another authorized event.

```text
redemption ──────┐
expiration ──────┤
revocation ──────┼──> retirement
cancellation ────┤
reconciliation ──┘
```

**Expiration** means that a policy-defined time or condition has made units no
longer valid for circulation or acceptance. **Revocation** is an exceptional
authority-initiated invalidation rather than an ordinary holder redemption.
Each requires an explicit enforcement and accounting design; neither should be
inferred merely from a memo or friendly label.

The current `retire` operation consumes presented Mint Notes, marks their
proofs spent, and records their amount as retired supply. Automatic expiration
and administrative revocation of unpresented bearer notes are not yet separate
implemented operations.

An issuer may currently state an expiry date in its external redemption policy
and use that date when deciding whether or how to honour a returned note. That
policy does not change proof validity: expiry is not encoded in the proof, is
not checked by swaps or proof-state endpoints, and does not automatically
retire outstanding units. Wallets may display the policy, but must not present
it as protocol enforcement.

Retirement does not imply a payout in Bitcoin, fiat, goods, or another asset.
Any external consequence must come from the issuer’s published policy.

## Preferred terminology

| Preferred term | Meaning |
| --- | --- |
| Mint | Cryptographic issuer and redeemer |
| Mint Note | Bearer instrument issued by a mint keyset |
| Transferable unit | General category for a fungible unit that can move between holders under an issuer's policy |
| Clear Mint Unit (CMU) | Keyset-defined unit of account |
| `cmu-<keyset-id>` | Canonical protocol unit identifier |
| Mint cluster | Approved mint instances serving one CMU with coordinated double-spend state |
| Denomination | Fixed amount represented by a Mint Note |
| Cashu proof | Technical representation of a spendable Mint Note |
| Redemption | Holder returns Mint Notes to the issuer for validation and consumption |
| Retirement | Generalized terminal outcome that permanently removes units from circulation |
| Expiration | Policy-defined time or condition after which units are no longer valid |
| Revocation | Exceptional authority-initiated invalidation rather than ordinary redemption |

Avoid **Treasury Note**, which already has an established meaning in government
debt markets. Treat older experimental unit identifiers as superseded
experimental vocabulary.
