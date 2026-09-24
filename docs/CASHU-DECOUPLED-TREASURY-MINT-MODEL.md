# Cashu Decoupled: Clear's Treasury Mint Model

Status: Architecture and positioning note

## Purpose

Clear is based on the Cashu protocol. Its defining architectural move is to
decouple Cashu's Chaumian bearer-note machinery from the Bitcoin and Lightning
settlement assumptions used by most Cashu mints.

This is not a claim to new blind-signature cryptography. Cashu supplies the
core protocol. Nor is it a claim that Cashu can support only Bitcoin: the Cashu
specifications permit multiple units and custom payment methods. The model
shift lies in what Clear makes authoritative.

In a conventional Bitcoin-backed Cashu mint, payment normally authorizes
issuance and redemption normally triggers payment. In Clear, institutional
policy and delegated treasury authority authorize issuance, while the policy
defines what redemption accomplishes.

```text
Cashu cryptographic protocol
  + issuer-defined treasury units
  + delegated treasurer authority
  + policy-governed issuance and redemption
  + multiple keyset-bound units per operating mint
  = Clear
```

## The retained Cashu protocol

Clear preserves the parts of Cashu that make private bearer ecash possible:

- blinded messages and blind signatures;
- denomination-specific signing keys grouped into keysets;
- wallet-held bearer proofs;
- proof splitting and combination through swaps;
- spent-proof state and double-spend prevention;
- mint discovery and public denomination keys;
- portable Cashu token encoding; and
- compatible request and proof data structures where applicable.

In Clear terminology, the holder-facing instrument is a **Mint Note**. A Cashu
proof remains the technical data structure representing one spendable Mint
Note. An exact Cashu keyset defines the canonical **Clear Mint Unit (CMU)**:

```text
cmu-<keyset-id>
```

Clear therefore does not replace Cashu. It specializes Cashu for a different
institutional purpose.

## The conventional payment-coupled model

Most deployed Cashu systems are oriented toward bitcoin and Lightning.

### Issuance

```text
wallet requests mint quote
  -> mint produces a Lightning or on-chain payment request
  -> wallet pays bitcoin
  -> mint confirms payment
  -> mint signs blinded outputs
  -> wallet receives sat-denominated ecash
```

The payment event supplies the economic authorization for issuance. The note
normally represents a custodial claim on bitcoin controlled by the mint.

### Redemption

```text
wallet presents ecash and a Lightning payment request
  -> mint verifies and spends the proofs
  -> mint pays bitcoin through Lightning
  -> the custodial claim is discharged
```

Cashu calls this operation melting. The payment rail and underlying asset give
the note a familiar settlement meaning.

This model is powerful, but it joins three functions:

1. the bearer-note protocol;
2. the asset held by the mint; and
3. the rail used to enter and leave the mint.

Clear separates them.

## The Clear treasury-authorized model

Clear replaces payment-triggered issuance with an authorization from an
institutionally recognized treasurer.

### Issuance

```text
currency or program authority establishes policy
  -> authority appoints a treasurer
  -> treasurer authorizes a bounded issuance for one exact CMU
  -> mint validates authority, policy, nonce, amount, and limits
  -> mint signs blinded Cashu outputs
  -> wallet receives Mint Notes
```

No Lightning invoice is required to establish that the issuance may occur.
The economic event may be a budget allocation, deposit of goods, recognition
of an obligation, grant of a benefit, purchase of services, warehouse
attestation, or another event defined outside the mint.

### Redemption and retirement

```text
holder presents Mint Notes to a recognized party
  -> mint validates and marks the Cashu proofs spent
  -> issuer performs the consequence defined by policy
  -> supply is retired or otherwise reconciled
```

The consequence might be delivery of goods, provision of a service,
reimbursement of a provider, release of warehouse inventory, consumption of
compute, conversion into another instrument, or simple closure of an internal
allocation.

Clear proves that valid Mint Notes were presented and prevents them from being
used again. The surrounding institution determines whether and how the
associated obligation is discharged.

## What changed

| Dimension | Typical Bitcoin-backed Cashu mint | Clear |
| --- | --- | --- |
| Protocol substrate | Cashu | Cashu |
| Normal unit | sat | Exact `cmu-<keyset-id>` |
| Issuance trigger | Confirmed bitcoin or Lightning payment | Signed treasury authorization under policy |
| Meaning of note | Custodial bitcoin claim | Issuer-defined credit, liability, entitlement, or unit |
| Redemption trigger | Request to pay bitcoin | Presentation under issuer policy |
| Redemption consequence | Bitcoin or Lightning payout | Policy-defined performance or retirement |
| Number of institutional units | Usually one principal sat unit per mint | Multiple distinct CMUs on one operating mint |
| Supply authority | Payment received by mint | Treasurer operating within delegated limits |
| Backing evidence | Bitcoin reserves and payment liquidity | Depends on CMU: budget, inventory, service capacity, obligation, reserves, or other policy evidence |
| Trust endpoint | Bitcoin custodian and mint operator | Issuer, treasurer, mint operator, redemption authority, and any custodian named by policy |

The bearer mechanics remain the same. The institutional contract around them
changes.

## Why this is more than a custom unit label

A Cashu implementation can advertise a different unit string or install a
custom payment backend. That alone does not create the Clear model.

Clear adds explicit answers to questions outside ordinary proof validation:

- Who is authorized to establish a currency or program?
- Who may create a new keyset and therefore a new CMU?
- Which treasurer may authorize issuance for that CMU?
- What amount, purpose, policy version, and replay protection bind the action?
- What does the unit represent?
- Who recognizes and redeems it?
- What evidence constrains supply?
- What does retirement mean for the issuer's books or obligations?
- How do multiple CMUs remain separate on one operating mint?

The difference is therefore governance and institutional semantics, not merely
configuration.

## From one reserve asset to many policy domains

Bitcoin-backed Cashu has a common reserve model: outstanding sat-denominated
ecash should correspond to bitcoin controlled by the mint.

Clear cannot use one universal backing statement because different CMUs can
represent different things:

| CMU type | Possible issuance basis | Possible redemption consequence |
| --- | --- | --- |
| Community food credit | Approved program budget | Provider reimbursement or recognized food delivery |
| Membership credit | Membership allocation or purchase | Club service or benefit |
| Compute unit | Funded service allowance | Metered inference, storage, or processing |
| State program unit | Appropriation or delegated program authority | Recognized public-purpose benefit |
| Clear Warehouse Unit | Eligible inventory capacity | Goods, warrant transfer, or sale proceeds |
| Corporate internal unit | Treasury allocation | Internal service, expense, or accounting settlement |

Every CMU therefore needs its own policy, authority, supply accounting,
acceptance domain, and risk disclosure. Two units served by the same software
are not interchangeable.

## The payment rail becomes optional

Decoupling does not mean Clear rejects Bitcoin, Lightning, banks, blockchains,
or other payment systems. It changes their role.

They can be used as:

- funding rails before a treasury allocation;
- settlement rails after redemption;
- exchange rails between distinct CMUs;
- payment methods for purchasing a CMU;
- reimbursement mechanisms for recognized providers; or
- interoperability paths alongside Clear balances in the same wallet.

They are no longer required to define the unit or authorize every mint and
redemption event.

```text
Payment-coupled model:
payment rail -> authority to issue -> bearer notes -> payment rail

Clear model:
issuer policy -> treasury authority -> bearer notes -> policy consequence
                       |                              |
                 optional funding              optional settlement rail
```

That inversion is the fundamental shift.

## From universal money assumptions to explicit recognition

A sat-denominated Cashu note inherits a broadly understood external unit and a
redemption expectation tied to bitcoin. A Clear Mint Note does not inherit
universal acceptance.

Its usefulness depends on endpoints that recognize the exact CMU and its
issuer. That is not an implementation defect. It is what permits one mint to
serve bounded communities and institutions without collapsing their promises
into a fictional universal balance.

Wallets must therefore show:

- the exact CMU identity;
- issuer and policy;
- mint or approved mint cluster;
- acceptance and redemption context;
- lifecycle state; and
- relevant backing, capacity, or risk evidence.

Friendly names remain presentation metadata. They must never replace the full
CMU identity.

## From account credit to portable bearer instrument

Organizations already issue credits, vouchers, benefits, allowances, service
units, and inventory claims. They usually implement them as rows in a central
account database.

Clear changes the possession model:

```text
Account model:
organization database says Alice owns 10

Clear model:
Alice's wallet holds Mint Notes totalling 10
```

The mint still prevents double spending, and redemption still depends on the
issuer. But ordinary transfers do not require the issuer to rewrite a named
sender and recipient balance. Blind signatures can also reduce the mint's
ability to link issuance with later redemption.

The resulting unit is credit-like in its institutional meaning and coin-like
in circulation.

## New responsibilities created by decoupling

Removing the fixed Bitcoin and Lightning settlement contract creates freedom,
but it also removes inherited answers. Clear must not imply that cryptography
supplies those answers automatically.

Each CMU needs policy for:

- legal and economic characterization;
- issuance basis and maximum supply;
- backing, inventory, budget, or service-capacity evidence;
- treasurer appointment and revocation;
- acceptance and redemption;
- expiry, suspension, conversion, and retirement;
- fees and operational service levels;
- insolvency, shortfall, and failed performance;
- audit and reconciliation; and
- dispute resolution and governing law.

Clear validates signatures and proofs. It cannot prove that an issuer will
honour a promise, that warehouse goods exist, or that a service will remain
available unless trusted institutional evidence connects those facts to the
CMU.

## Compatibility boundary

Clear should remain recognizably Cashu wherever the Cashu protocol already
solves the problem:

- proof construction and verification;
- key discovery and keyset identity;
- swaps and spent-state checks;
- token encoding; and
- compatible payment-request structures.

Clear-specific extensions should remain concentrated at the institutional
boundary:

- root and treasurer authority;
- CMU creation grants;
- the experimental `clear` mint method;
- signed issuance and retirement authorizations;
- policy descriptors and lifecycle state;
- multi-CMU separation; and
- policy-aware supply and backing metrics.

This boundary preserves ecosystem compatibility without pretending that a
standard Bitcoin-oriented wallet already understands Clear's institutional
semantics.

## Positioning statement

The recommended concise description is:

> Clear is a Cashu-based Chaumian mint that decouples private bearer ecash from
> Bitcoin and Lightning settlement and places issuance, redemption, and unit
> meaning under explicit treasury policy.

For technical audiences:

> Clear preserves Cashu proofs, keysets, swaps, and spent-state validation. It
> replaces payment-triggered issuance and melt-to-payment redemption with
> signed treasurer authorization and policy-defined redemption for exact,
> keyset-bound Clear Mint Units.

For institutional audiences:

> Clear lets an organization mint private, portable bearer units without
> making a blockchain or payment rail the authority that defines those units.

## Conclusion

Cashu demonstrated that Chaumian ecash can be practical, interoperable, and
simple enough for modern wallets and mints. Clear begins with that achievement.

The fundamental shift is to treat the bearer-note protocol as independent
infrastructure. Bitcoin and Lightning become optional assets and rails rather
than mandatory sources of institutional meaning. Treasury authority can then
issue many kinds of exact, bounded units while retaining Cashu's privacy and
double-spend protections.

That makes Clear neither a new cryptographic protocol nor merely a renamed
Cashu mint. It is a treasury-governed application of Cashu to a wider class of
issuer-defined value.

