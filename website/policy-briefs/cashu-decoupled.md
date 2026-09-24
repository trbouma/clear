---
title: Cashu, Decoupled
description: How Clear preserves Cashu's private bearer ecash while moving issuance and redemption from payment rails to treasury policy.
---

# Cashu, Decoupled

Clear is based on the Cashu protocol. It uses Cashu's blind signatures,
keysets, bearer proofs, swaps, and spent-proof state.

Its defining move is not a new cryptographic mechanism. It is an institutional
change:

> Clear decouples Cashu's private bearer ecash from Bitcoin and Lightning
> settlement and places issuance, redemption, and unit meaning under explicit
> treasury policy.

That turns a payment-backed ecash mint into general-purpose digital minting
infrastructure for communities, corporations, public programs, warehouses,
and software-agent economies.

## What Cashu provides

Cashu provides the machinery needed for private digital bearer notes:

- a wallet blinds messages before asking the mint to sign them;
- the mint signs without learning the resulting spendable proofs;
- holders carry and transfer the proofs;
- wallets swap proofs into fresh denominations; and
- the mint records spent secrets to prevent double spending.

Clear calls the resulting bearer instruments **Mint Notes**. Their technical
representation remains Cashu proofs.

Clear does not replace this protocol. It changes the institutional contract at
the mint boundary.

## The usual Bitcoin and Lightning loop

Most Cashu mints are built around a familiar cycle:

```text
bitcoin payment received
  -> sat-denominated ecash issued
  -> ecash circulates privately
  -> ecash returned
  -> Lightning or bitcoin payment made
```

Payment authorizes issuance. Payment also gives redemption its meaning. The
ecash normally represents a custodial claim on bitcoin held by the mint.

That model joins the bearer protocol, reserve asset, and settlement rail.

## The Clear loop

Clear separates those functions:

```text
issuer establishes policy
  -> authorized treasurer approves issuance
  -> CMU Mint Notes circulate privately
  -> recognized party accepts the notes
  -> redemption or retirement follows policy
```

No Lightning invoice is required to authorize issuance. The event behind the
issuance might instead be a budget allocation, member entitlement, service
allowance, warehouse deposit, program benefit, or compute allocation.

Redemption might produce goods, services, reimbursement, inventory release,
compute consumption, conversion, or closure of an internal obligation.

The mint proves that valid notes were presented and prevents their reuse. The
issuer's policy determines what is owed.

## Same protocol, different authority

| Question | Typical Bitcoin-backed Cashu mint | Clear |
| --- | --- | --- |
| What authorizes issuance? | Confirmed payment | Signed treasurer action under policy |
| What is issued? | Usually sat-denominated ecash | Exact keyset-bound Clear Mint Unit (CMU) notes |
| What does the note represent? | Custodial bitcoin claim | Issuer-defined credit, liability, entitlement, or unit |
| What happens at redemption? | Bitcoin or Lightning payout | Policy-defined performance and retirement |
| What provides backing? | Bitcoin controlled by the mint | Budget, goods, services, reserves, authority, or other evidence defined per CMU |
| How many units can one mint serve? | Usually one principal sat unit | Many institutionally separate CMUs |

The complete CMU identity remains `cmu-<keyset-id>`. Two notes served by the
same software are not interchangeable merely because their friendly names or
denominations resemble one another.

## Why this is not just a custom payment backend

A different unit label or payment adapter does not answer the institutional
questions Clear is designed to make explicit:

- Who may establish the unit?
- Who appoints its treasurer?
- Who may create its keyset and authorize supply?
- What does the unit represent?
- Where is it accepted?
- What constrains issuance?
- What does redemption accomplish?
- Who bears the loss if the promise fails?

Clear separates these responsibilities from routine mint operation. The root
authority establishes policy and delegates. The treasurer authorizes supply
actions. The mint operator protects keysets and spent state. The issuer or
redemption authority performs the real-world promise.

## Payment rails become optional tools

Decoupling does not exclude Bitcoin, Lightning, bank payments, or blockchains.
It changes their role.

They may fund a program before issuance, reimburse a provider after
redemption, exchange one CMU for another, or coexist with Clear balances in the
same wallet. They no longer have to be consulted every time the treasury mints
or retires its own unit.

```text
payment-coupled ecash:
rail -> issuance -> bearer notes -> rail

Clear:
policy -> authority -> bearer notes -> policy consequence
          ^                              |
          |------ optional rails --------|
```

This makes the payment rail a service to the treasury rather than the source
of the treasury's authority.

## A broader class of instruments

Once Cashu is separated from a single reserve asset and settlement rail, the
same bearer machinery can support:

- community and program vouchers;
- corporate service and benefit units;
- public-purpose or state-recognized units;
- compute credits for software agents;
- hospitality and membership credits;
- warehouse entitlements; and
- other policy-defined claims.

The freedom comes with responsibility. Every CMU needs its own issuance basis,
redemption promise, supply limits, lifecycle, risk disclosures, and audit
evidence. Cryptographic scarcity does not prove that inventory exists or that
an issuer will perform.

## The model shift

Conventional digital-payment systems generally begin with an existing unit and
ask how to move it. Clear begins with the institution:

```text
Who has authority?
What may they issue?
What promise does the unit carry?
Who recognizes it?
How does the obligation end?
```

Cashu then gives the answer a private, portable, coin-like form.

This is why Clear should be understood as a treasury-governed application of
Cashu, not a competing ecash protocol and not merely a Bitcoin mint with a
different backend.

## The policy takeaway

Cashu proved the bearer mechanism. Clear changes what the mechanism can serve.

> Cashu supplies private digital notes. Clear lets distinct institutions
> define, authorize, issue, and redeem those notes as their own exact treasury
> units.

For the detailed architecture and compatibility analysis, see
[Cashu Decoupled: Clear's Treasury Mint Model](https://github.com/trbouma/clear/blob/main/docs/CASHU-DECOUPLED-TREASURY-MINT-MODEL.md).

