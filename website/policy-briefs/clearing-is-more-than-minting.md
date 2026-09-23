---
title: Clearing Is More Than Minting
description: What the London Metal Exchange rulebook reveals about Clear's place in a wider clearing and settlement scheme.
---

# Clearing Is More Than Minting

The name **Clear** invites an important question: does a Clear mint perform
“clearing” in the same sense as a financial-market clearing house?

The short answer is no. It performs a narrower function that could become a
useful part of a wider clearing and settlement scheme.

The London Metal Exchange (LME) rulebook makes the distinction unusually
clear. Its scheme separates trade formation, clearing, margin, payment,
delivery, warehouse custody, default management, and dispute resolution. A
payment or delivery instrument participates in that structure, but it does not
replace the structure.

## Clearing transforms obligations

In the LME scheme, an agreed trade is not automatically a cleared contract.
The Clearing House must accept it under separate rules. Clearing can then
replace, transfer, novate, compress, net, or settle-to-market contractual
positions.

The Clearing House also manages risk before final performance. Members must
meet margin and payment obligations. If a member defaults, rules determine how
positions may be valued, discharged, transferred, or netted.

That is the broad institutional meaning of clearing:

```text
trade
  -> acceptance into clearing
  -> counterparty and position management
  -> margin, netting, and payment obligations
  -> settlement by offset, cash, or delivery
  -> default process if performance fails
```

Clearing is not simply checking whether a digital object has already been
spent.

## What Clear actually does

Clear provides Chaumian minting infrastructure. An authorized treasurer can
issue private bearer Mint Notes denominated in an exact Clear Mint Unit (CMU).
Holders can possess and transfer those notes. The mint validates proofs,
prevents double spending, supports swaps, and accepts notes for redemption or
retirement under the issuer's policy.

```text
issuer policy
  -> treasurer-authorized issuance
  -> private bearer circulation
  -> mint spent-proof validation
  -> redemption or retirement
```

That is a meaningful form of instrument administration. It is not trade
matching, contract novation, portfolio netting, margin calculation, asset
custody, or default management.

The distinction protects Clear from making the wrong promise. A mint can prove
that a note is valid and unspent. It cannot, through cryptography alone, prove
that a warehouse holds metal, that reserves are sufficient, that a contract
has been legally discharged, or that losses will be absorbed if an issuer
fails.

## The warehouse-warrant lesson

The LME's LMEsword system electronically creates, transfers, withdraws, and
cancels warehouse warrants. Those warrants are tied to metal held by approved
warehouses. Their legal effect depends on the Exchange's rules, warehouse and
depository obligations, operating procedures, and applicable law.

This resembles a mint lifecycle only at a high level:

| LMEsword | Clear |
| --- | --- |
| Warehouse causes a warrant to be created | Treasurer authorizes Mint Note issuance |
| System transfers a recognized metal entitlement | Holders transfer bearer proofs |
| Withdrawal or cancellation closes a warrant lifecycle | Redemption or retirement closes a Mint Note lifecycle |
| Rules prevent conflicting warrant claims | Spent-proof state prevents double spending |

The difference is decisive. A warrant concerns identified metal and legal
title or bailment rights. A Mint Note is a fungible amount whose meaning comes
from a CMU policy. Calling a CMU “copper” does not make it a warehouse warrant.

Clear may be better suited to the fungible cash or credit side of an exchange,
while an authoritative registry continues to control unique assets and title.

## Where Clear fits

Clear can sit at the settlement edge of a broader scheme.

An external system can determine that an obligation exists. The payer can
transfer Mint Notes in the required CMU. The recipient can validate or redeem
them. The governing scheme can then recognize that evidence as satisfying the
obligation.

```text
scheme determines what is owed
  -> Clear carries the settlement instrument
  -> recipient validates or redeems it
  -> scheme records discharge or an exception
```

This pattern is immediately relevant to community vouchers, corporate units,
public-interest programs, and compute credits for agents. Clear supplies
private bearer circulation between issuance and redemption. The organization
supplies the institutional meaning at those endpoints.

It could also support a prefunded settlement instrument or the fungible leg of
a delivery-versus-payment arrangement. Those uses would require more than a
mint API: backing controls, reconciliation, participant rules, operational
resilience, failure handling, and a clear statement of when settlement becomes
final.

## Four meanings that should not be collapsed

Clear documentation and integrations should keep four events distinct:

- **Proof accepted**: the mint accepted a valid, unspent proof.
- **Mint Note retired**: the accepted proof was removed from circulation.
- **Redeemed under policy**: the issuer performed the consequence promised by
  the CMU policy.
- **Obligation discharged**: the governing external scheme recognizes that no
  further performance is owed.

Those events may occur together in a simple voucher program. In a larger
market arrangement, they may involve different systems, actors, and times.

## The policy opportunity

Clear should not be positioned as a miniature central counterparty or as a
replacement for a mature clearing house. Its opportunity is more specific and,
in many settings, more interesting.

Clear allows a treasury or recognized authority to issue a private bearer
instrument that can circulate between controlled endpoints of trust. The unit
can be used by a wider scheme without forcing every intermediate transfer onto
the scheme's account ledger.

The surrounding institution still defines:

- who may issue and accept the unit;
- what obligation or entitlement it represents;
- whether it is backed and how backing is verified;
- what redemption accomplishes;
- when settlement is final; and
- what happens when an issuer, custodian, or participant fails.

Clear contributes minting, privacy, portable possession, and double-spend
protection. A clearing arrangement contributes contract transformation, risk
management, legal effect, and failure procedures.

## The policy takeaway

The broader meaning of clearing gives Clear a sharper position:

> Clear is Chaumian minting and settlement-instrument infrastructure. It can
> participate in a clearing scheme without claiming to be the clearing scheme.

That boundary is not a limitation to hide. It is the basis for credible
integration. It lets communities, corporations, and public institutions adopt
a private bearer medium while keeping responsibility for contracts, custody,
settlement finality, and default exactly where those responsibilities belong.

For the detailed analysis, see
[LME Clearing, Settlement Infrastructure, and Clear](https://github.com/trbouma/clear/blob/main/docs/LME-RULEBOOK-CLEARING-AND-CLEAR-ANALYSIS.md).

