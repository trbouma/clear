---
title: The Unit Before the Rail
description: What The Great Rail Shift reveals about Clear's role beyond stablecoin and bank payment infrastructure.
---

# The Unit Before the Rail

*The Great Rail Shift* describes a financial system in transition. Stablecoins,
tokenized deposits, banks, market makers, custodians, and clearing mechanisms
are beginning to form a layered infrastructure for cross-border payments.

Its conclusion is not that blockchains will replace banks. Stablecoins are more
likely to become an intermediate settlement layer connecting regulated
endpoints.

That argument matters for Clear because it clarifies the difference between a
**rail** and a **mint**.

> A rail moves an existing unit. Clear defines how an institution may create,
> circulate, and redeem its own exact bearer unit.

## Moving money is increasingly modular

The report shows that one cross-border payment may involve several systems:

```text
local bank account
  -> stablecoin or tokenized deposit
  -> market maker or foreign-exchange venue
  -> blockchain transfer
  -> destination bank account
```

The winning infrastructure may be hybrid. Banks provide regulated accounts,
trust, screening, credit, and liquidity. Stablecoins provide programmable,
rapid transfer. Market makers provide conversion. Clearing mechanisms connect
otherwise fragmented instruments.

Clear should be able to use all of them. It should not be defined by any one of
them.

## Clear starts one question earlier

Stablecoin infrastructure generally begins with dollars, euros, or another
established monetary unit and asks how to move it more efficiently.

Clear begins with institutional authority:

```text
Who may establish the unit?
Who may issue it?
What does it represent?
Where is it recognized?
What does redemption accomplish?
```

An authorized treasurer then issues private bearer Mint Notes denominated in a
specific Clear Mint Unit (CMU). Holders can carry and transfer the notes, while
the mint prevents double spending. The issuer's policy defines acceptance and
redemption.

## Cashu without a mandatory settlement rail

Clear is based on the Cashu protocol. It preserves blind signatures, keysets,
bearer proofs, swaps, and spent-proof state.

Most Cashu mints use a payment-coupled loop:

```text
bitcoin or Lightning payment
  -> private ecash
  -> bitcoin or Lightning payment
```

Clear decouples the bearer-note machinery:

```text
issuer policy
  -> treasury authorization
  -> private Mint Notes
  -> policy-defined redemption
```

A bank or stablecoin payment may fund issuance or settle a provider after
redemption. A warehouse may release goods. A compute service may consume an
allowance. These are adapters at the edge, not the source of the CMU's
identity.

## Issuing a unit does not create its market

One of the report's strongest observations is that issuing a token is not the
same as creating a market for it.

The same is true for Clear. A CMU needs:

- holders willing to accept issuer risk;
- providers that recognize it;
- reliable redemption;
- understandable supply and backing evidence;
- distribution into a real community of use; and
- explicit conversion arrangements where liquidity is needed.

Technical transferability is necessary, but it is not economic usefulness.

## Clear does not seek singleness by default

Stablecoin clearing often seeks par conversion among tokens representing the
same national currency. Its goal is “singleness of money.”

Clear begins with a different safety rule: distinct promises must remain
distinct.

```text
cmu-<keyset-id>
```

The complete keyset-bound identifier defines the unit. A community food credit,
warehouse wheat unit, corporate service credit, and compute allowance are not
interchangeable because they share a mint or friendly label.

Conversion can exist, but it must be an explicit quoted transaction. Clear
should never obtain interoperability by erasing issuer, policy, or redemption
differences.

## A better model for funded agents

The report argues that agentic payments need delegated authority, verifiable
intent, permission controls, and limited blast radius.

Clear adds another tool: bounded bearer value.

```text
principal funds an agent with 1,000 compute CMU
  -> agent spends or delegates Mint Notes
  -> service redeems notes as work is performed
  -> agent cannot spend more than it controls
```

An identity framework can prove who the agent represents. Mint Notes can bound
the value placed under the agent's control. These functions complement each
other without requiring every intermediate transfer to reveal a complete
identity chain.

## Commodity trade has two legs

The report identifies payment settlement as a major source of friction in
physical commodity trade. Stablecoins may improve the cash leg.

Clear Warehouse Units could address the entitlement leg:

| Cash leg | Commodity leg |
| --- | --- |
| Bank payment or stablecoin | Clear Warehouse Unit |
| Foreign-exchange liquidity | Certified inventory pool |
| Payment settlement | Warrant transfer or physical delivery |

These legs still need coordination. A blockchain transfer is not proof that
goods were delivered, and a retired Mint Note is not by itself physical
load-out. The governing scheme must define finality and partial-failure rules.

## What Clear should build for the rail shift

Clear should remain narrow at its core and explicit at its boundaries:

- Cashu for private bearer notes;
- treasury policy for authority and unit meaning;
- exact CMUs for institutional separation;
- adapters for banks, stablecoins, Bitcoin, Lightning, warehouses, and
  enterprise systems;
- distinct evidence for proof acceptance, retirement, external settlement,
  and obligation discharge; and
- policy-aware metrics that do not mistake swaps or automated activity for
  economic use.

## The policy takeaway

The emerging financial system may contain many rails. Clear does not need to
choose one winner.

Its role is to make the instrument portable across them while preserving the
issuer's authority and the holder's privacy:

> The rail shift makes value movement modular. Clear makes the unit itself
> institutionally programmable.

For the detailed analysis, see
[The Great Rail Shift and Clear](https://github.com/trbouma/clear/blob/main/docs/THE-GREAT-RAIL-SHIFT-CLEAR-ANALYSIS.md).

Read the original report:
[The Great Rail Shift: Convergence between Legacy Infrastructure and Stablecoin Rails (PDF)](../assets/sources/The-Great-Rail-Shift.pdf).
