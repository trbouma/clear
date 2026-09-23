# LME Clearing, Settlement Infrastructure, and Clear

Status: Analysis note

## Purpose and scope

This note analyzes the London Metal Exchange (LME) *Rules and Regulations*,
dated 21 September 2026, to clarify how Clear might fit within a mature market
scheme and why the word **clearing** has a broader institutional meaning than
the function currently performed by the Clear mint.

The rulebook is useful because it does not describe one undifferentiated
transaction system. It separates trading, contract formation, clearing,
payment, delivery, warehouse custody, default management, and dispute
resolution. That separation exposes the boundaries around Clear.

Clear currently provides cryptographic minting infrastructure for private
bearer instruments. An authorized treasurer can cause Mint Notes denominated
in a specific Clear Mint Unit (CMU) to be issued. Holders can transfer those
notes, and the mint can validate proofs, prevent double spending, support
swaps, and accept notes for redemption or retirement. Those are useful
functions, but they are not the whole of market clearing.

This is a technical and institutional comparison, not legal advice. The LME
rulebook also incorporates separate Clearing House Rules and operating
procedures. Because those documents are not part of the supplied source, this
note does not purport to describe every LME Clear process or legal effect.

## Executive finding

The LME scheme supports a precise conclusion:

> Clear can mint and administer a bearer instrument that may be used within,
> alongside, or at the boundary of a clearing scheme. Clear is not, by that
> fact alone, a clearing house.

In the LME rulebook, clearing transforms and manages obligations. It includes
accepting a trade into the clearing system, creating or replacing contracts,
netting positions, collecting margin, administering payments, coordinating
delivery, managing a member default, and preserving enforceable records and
rights. Settlement then discharges the resulting obligations through cash,
delivery, set-off, or other recognized performance.

Clear's present mechanism addresses a different layer:

```text
issuer policy and treasurer authority
  -> minting of bearer Mint Notes
  -> holder possession and transfer
  -> spent-proof validation and swap
  -> redemption or retirement under issuer policy
```

The mint can establish whether a presented proof is valid and unspent. It does
not presently determine whether a trade is eligible for clearing, become the
counterparty to that trade, calculate margin, net a portfolio, deliver a
specific warehouse warrant, or administer a member default.

The best near-term fit is therefore **settlement-instrument infrastructure at
the edge of a scheme**, especially for bounded communities, corporations, or
public-interest programs whose governing authority defines the unit and its
redemption. More ambitious uses inside regulated market infrastructure would
require explicit integration with the institutions that supply contract,
custody, delivery, risk, and legal-finality functions.

## What “clearing” means in the LME scheme

### From agreed trade to cleared contract

Part 1 of the rulebook distinguishes an **Agreed Trade** from a **Cleared
Contract**. A trade contains the particulars agreed by the trading parties. A
Cleared Contract may result only after the acceptance process under the
Clearing House Rules. The definition also reaches contracts created by
processes that vary, transfer, replace, novate, port, net, or settle-to-market
earlier contracts.

This is much broader than validating a payment object. Clearing changes the
legal and risk structure around an obligation. The resulting contract may no
longer be simply the original bilateral bargain in its original form.

The rulebook reinforces that point through its definitions of compression and
position netting. Multiple contracts may be aggregated, opposing positions may
be netted, and replacement contracts may be created. A clearing system is
therefore concerned with a portfolio of obligations over time, not merely a
single transferable unit.

### Risk management before final performance

The scheme uses initial margin and variation margin, closing prices, daily
settlement prices, and position-management rules. Part 3, Regulation 6 connects
published closing prices with margin calculations. Regulation 7 requires every
Clearing Member to make the arrangements necessary to participate in the
payment system administered by the Clearing House.

These functions exist because performance may be due in the future and the
value of an open position can change before settlement. Clearing manages that
exposure before the final payment or delivery occurs.

A Clear Mint Note does not currently represent a margined derivatives
position. It represents a spendable bearer claim or entitlement whose meaning
comes from the CMU policy. Clear can account for issuance and retirement, but
it does not calculate a member's current exposure or mutualize the risk of
future non-performance.

### Settlement by offset, cash, or delivery

Part 3, Regulation 9 provides for settlement of contracts by offset or by
delivery and for settlement of price differences. The applicable settlement
path depends on the type of contract and the rules governing it. Settlement is
not synonymous with payment: it can include the delivery of an asset-side
entitlement as well as a cash-side amount.

Part 3, Regulation 10 and Part 10 connect physical settlement to LME warehouse
warrants. A seller may satisfy delivery obligations by transferring qualifying
warrants through LMEsword. Those warrants relate to identified metal held by a
listed warehouse and carry legal effects defined by the rulebook, warehouse
agreements, operating procedures, and applicable law.

This reveals three distinct layers:

```text
contract obligation
  -> clearing and risk transformation
  -> settlement instruction
  -> cash payment and/or delivery of a recognized asset entitlement
```

Clear is most naturally considered at the last layer, as a possible form for a
settlement instrument, not as a substitute for all four layers.

### Default is part of clearing

Part 9 treats failure to pay, deliver warrants, or satisfy margin as events of
default. It provides for the management, discharge, valuation, transfer, and
netting of unsettled contracts, as well as coordination with the Clearing
House and other bodies.

This is not an exceptional detail. A clearing arrangement is defined partly by
what happens when an expected performance does not occur. It needs authority
to identify a default, value obligations, preserve or port positions, use
collateral, and establish the resulting net amount.

Clear has narrower failure semantics. It can reject an invalid or already
spent proof, suspend new treasury mutations, or place a CMU into a constrained
lifecycle state. It does not currently close out a member's portfolio, port a
client position, calculate a default settlement amount, or allocate losses.

## LMEsword: an especially useful comparison

LMEsword is closer to Clear than the trading venue or central counterparty
functions, but the similarities should be handled carefully.

Part 10 says that LMEsword provides for the creation, withdrawal, and
electronic transfer of warrants and, through transfer, the constructive
delivery of underlying metal held by a warehouse. A warrant can function as a
document of title or as a record of bailment rights, depending on the relevant
jurisdiction. The system defines eligible participants, accounts, depository
and warehouse roles, creation controls, transfer instructions, withdrawal,
cancellation, invalidity, replacement, and legal effect.

There is a real conceptual resemblance:

| LMEsword concept | Clear analogue | Important difference |
| --- | --- | --- |
| Warehouse causes a warrant to be created | Treasurer authorizes Mint Note issuance | A warrant relates to identified metal; a Mint Note is a fungible amount under a CMU policy |
| Warrant transfer changes the recognized holder or bailment position | Mint Note transfer changes possession of bearer proofs | Clear intentionally does not maintain named holder accounts for private transfers |
| Duplicate or outside-system title claims are controlled by rule | Spent-proof state prevents reuse of a proof | Double-spend prevention does not itself establish legal title to an external asset |
| Withdrawal and cancellation close the electronic lifecycle | Redemption and retirement close the Mint Note lifecycle | Clear policy determines the consequence; physical delivery is not built in |
| Exchange, depository, and warehouse have separate obligations | Currency authority, treasurer, and mint operator have separate roles | Clear does not currently include a statutory depository or warehouse framework |
| Cleared warrant transfers can satisfy delivery obligations | A CMU could be recognized as a settlement instrument | Recognition must come from the external scheme; Clear cannot declare delivery legally complete |

The most important difference is instrument structure. An LME warrant is tied
to specific underlying metal, warehouse facts, weight, brand, and legal
relationships. Ordinary Clear Mint Notes are fungible denominations within a
CMU. A CMU called “one tonne of copper” would not, merely by its label, become
a warehouse warrant or convey title to a particular lot.

Representing warehouse claims in Clear would require a policy and registry
that prevent over-issuance, bind each issued amount to authoritative inventory,
handle lot-specific attributes, preserve required transfer restrictions, and
give redemption an enforceable consequence. Where uniqueness matters, a
fungible Chaumian token may be the wrong primary representation. Clear could
instead be used for the fungible cash or credit leg while an authoritative
warrant system continues to carry the asset leg.

## A functional map

The LME rulebook suggests separating the overall scheme into functions rather
than asking whether Clear “does clearing” as a single yes-or-no question.

| Scheme function | LME allocation visible in the rulebook | Clear today | Possible Clear role |
| --- | --- | --- | --- |
| Define eligible products and contracts | Exchange rules and contract specifications | CMU policy defines a unit, not a market contract | Publish machine-readable unit and redemption policy |
| Match or record trades | LME venues and Matching System | Not provided | Integrate with an external order, procurement, or entitlement system |
| Accept obligations into clearing | Clearing House under its rules | Not provided | Receive an authorized settlement instruction only after external acceptance |
| Replace, novate, compress, or net contracts | Clearing House and Exchange rules | Not provided | No near-term role; preserve this boundary |
| Calculate margin and manage exposure | Clearing House, prices, and member arrangements | Not provided | Potentially mint a separately governed collateral unit, but not calculate exposure |
| Administer payment arrangements | Clearing House payment system | Issuance and redemption APIs | Supply a recognized bearer settlement unit through an adapter |
| Deliver asset-side entitlement | LMEsword warrant transfer | No title or custody registry | Use another system for unique assets; consider Clear only for fungible entitlements with explicit legal backing |
| Prevent duplicate use | Account and warrant-transfer controls | Spent-proof state | Strong direct fit at the instrument layer |
| Establish settlement consequence | Contract, clearing, LMEsword, and applicable law | Issuer-defined redemption and retirement | Emit evidence; external rules must state its legal and accounting effect |
| Manage participant default | Exchange and Clearing House default rules | Proof rejection and lifecycle controls only | Provide auditable state, suspension, and redemption controls to the responsible authority |
| Resolve disputes and correct errors | Rulebook, arbitration, operating procedures | Limited technical error handling | Supply signed evidence without pretending code resolves the dispute |

## Where Clear could fit

### 1. A bounded settlement instrument

An organization or community can define a CMU as a recognized instrument for
discharging a narrow class of obligations. The scheme determines who may issue
it, who accepts it, what redemption means, and whether finality occurs at
receipt, mint validation, or redemption.

```text
external scheme determines obligation
  -> authorized party requests settlement
  -> payer transfers Mint Notes
  -> recipient validates or swaps them at the mint
  -> recipient redeems under the scheme policy
  -> external system records discharge
```

This is the clearest fit for community vouchers, corporate internal units,
state-recognized program credits, and agent compute credits. Clear supplies
the portable private instrument; the surrounding scheme supplies the
obligation and its legal or accounting consequence.

### 2. A prefunded instrument at the edge of central clearing

A clearing or procurement system might accept a CMU that represents a
prefunded claim on a treasury. The prefunding can reduce issuer credit risk,
but only if governance and operations make the claim credible. The scheme
would need assurance about issuance limits, backing, redemption, mint
availability, key custody, and insolvency treatment.

Clear could expose policy-aware supply metrics and signed lifecycle evidence.
It should not claim that cryptographic scarcity proves reserve sufficiency.
Mint-note supply and treasury assets are different facts and require
reconciliation.

### 3. A cash or credit leg beside an asset registry

For delivery-versus-payment, Clear could represent the fungible payment or
credit leg while a separate authoritative system controls the unique asset or
warrant leg. An orchestration layer would coordinate the two.

Clear does not currently provide atomic delivery-versus-payment. A production
integration would need a defined failure policy for partial completion,
timeouts, reversals, and disputes. Chaumian privacy also means that the mint
does not naturally know the identities of both transacting parties, so any
participant-eligibility checks must be located deliberately at wallet,
gateway, redemption, or scheme boundaries.

### 4. A privately circulating claim between clearing moments

The strongest conceptual opportunity may be between formal account-based
events. A scheme can issue a bearer claim at one controlled boundary, allow it
to circulate privately, and accept it back at another controlled boundary.
Only issuance and redemption need to touch the authoritative institutional
ledger.

That resembles coinage without claiming that every intermediate transfer is a
cleared market transaction. Clear provides privacy and holder agency between
the endpoints of trust; the scheme retains authority over entry and exit.

## What Clear must not imply

The name “Clear” is useful, but documentation should distinguish three ideas:

1. **Proof clearing**: the mint determines whether a bearer proof is valid and
   unspent, and records it as spent when accepted.
2. **Settlement-instrument administration**: the mint issues, swaps, redeems,
   and retires units under a treasury policy.
3. **Market clearing**: an institution accepts and transforms contractual
   obligations, manages counterparty exposure, nets positions, collects
   margin, coordinates settlement, and handles default.

Clear performs the first and much of the second. It does not currently perform
the third. Public positioning should say that plainly.

Terms such as “settled,” “cleared,” and “final” should therefore be qualified:

- **proof accepted** means the mint accepted an unspent proof;
- **Mint Note retired** means the proof was removed from circulation;
- **redeemed under policy** means the issuer performed the consequence stated
  by the CMU policy; and
- **obligation discharged** should be used only where the governing external
  rules give the event that effect.

## Institutional roles should remain separate

An integration should identify at least the following roles:

| Role | Responsibility |
| --- | --- |
| Scheme authority | Defines obligations, eligibility, acceptance, finality, and dispute rules |
| Clearing house or obligation manager | Accepts, nets, novates, margins, or otherwise manages contractual exposures |
| Currency or program authority | Defines the CMU and appoints treasurers |
| Treasurer | Authorizes issuance, redemption, and retirement within policy |
| Mint operator | Runs the protocol, protects keysets, signs blinded outputs, and maintains spent-proof state |
| Custodian or depository | Holds backing assets or authoritative asset records where the policy requires them |
| Wallet or gateway | Holds Mint Notes and may enforce participant or transaction rules at the edge |
| Auditor or oversight body | Reconciles policy, supply, backing, authority, and exceptional actions |

One organization may occupy more than one role, but the records should not
silently merge them. In particular, operating the mint should not confer the
power to define the obligation being settled or to declare a legal default.

## Requirements for deeper clearing integration

Before a regulated or systemically important scheme could rely on a Clear CMU,
the following capabilities would need explicit designs and accountable owners:

- legal characterization of the Mint Note and the holder's claim;
- participant eligibility and sanctions controls where required;
- issuance limits, backing rules, and independent reconciliation;
- segregation of house, client, and collateral interests where applicable;
- redemption service levels and an outage or recovery procedure;
- key compromise, key rotation, and mint-cluster consistency controls;
- settlement finality and the exact moment an obligation is discharged;
- delivery-versus-payment coordination and partial-failure handling;
- correction, invalidation, suspension, and court-order processes;
- insolvency and default treatment for the issuer, mint operator, custodian,
  wallet provider, and participant;
- portability or recovery if a mint operator fails;
- evidence retention compatible with privacy and audit obligations; and
- governance for rule changes, emergency powers, and dispute resolution.

Some requirements pull against pure bearer privacy. That tension should be
designed, not obscured. A scheme can preserve private transfers while applying
identity controls at issuance and redemption, but that is a policy choice with
specific surveillance, fungibility, and exclusion consequences.

## Recommended architecture boundary

The safest integration pattern is an adapter between Clear and an external
scheme of record:

```text
trade, procurement, or entitlement system
                 |
                 v
      obligation/clearing engine
                 |
       authorized settlement instruction
                 |
                 v
        Clear integration adapter
       /                         \
      v                           v
Clear mint and spent state     scheme audit record
      |                           |
      v                           v
holder transfer/redemption   discharge or exception decision
```

The adapter should carry a unique external obligation identifier, exact CMU,
authorized amount, policy version, expiry, and permitted completion evidence.
It should never include bearer secrets in the external audit record. Instead,
it should record signed issuance or redemption receipts and the minimum data
needed to reconcile the obligation.

Clear remains responsible for Mint Note validity and spent state. The external
scheme remains responsible for deciding what was owed, whether the settlement
event satisfies it, and what happens when performance fails.

## Product and documentation recommendations

1. Describe Clear as **Chaumian minting and settlement-instrument
   infrastructure**, not as a general-purpose clearing house.
2. Add explicit lifecycle terms for `proof accepted`, `redeemed`, `retired`,
   and `obligation discharged` rather than using “cleared” for all of them.
3. Extend CMU policy metadata with the issuer, eligible uses, redemption
   consequence, settlement-finality rule, backing or non-backing statement,
   governing law, and responsible dispute channel.
4. Produce signed, non-identifying issuance and redemption receipts suitable
   for external reconciliation without exposing bearer proofs.
5. Keep unique asset registries outside the fungible CMU model unless a
   dedicated design establishes authoritative title and lot identity.
6. Define a settlement-adapter contract before implementing integrations with
   procurement, benefits, state programs, agent funding, or market systems.
7. Treat margin, netting, novation, default management, and loss allocation as
   separate institutional services, even if Clear Mint Notes are accepted as
   one form of collateral or settlement value.

## Conclusion

The LME rulebook does not diminish the Clear model. It locates it.

A mature market separates the instrument, the obligation, the institution
that manages counterparty risk, the payment mechanism, the asset-delivery
system, and the rules for failure. Clear offers a new form for one important
part of that stack: an issuer-defined, privately transferable bearer unit with
cryptographic issuance and spent-proof control.

That unit can make a broader scheme more flexible. It can circulate between
controlled issuance and redemption boundaries, represent a prefunded claim,
or provide the fungible leg of an exchange. But the surrounding authority must
still say what the unit means, which obligations it can discharge, how assets
are held, when settlement is final, and what happens on default.

The durable positioning is therefore not “Clear performs every kind of
clearing.” It is:

> Clear gives treasuries and recognized authorities a private bearer
> instrument that can participate in a larger clearing and settlement scheme
> without pretending that the instrument replaces the scheme.

## Source references

The analysis relies principally on the following provisions of the supplied
LME *Rules and Regulations*, dated 21 September 2026:

- Part 1 definitions of Agreed Trade, Cleared Contract, Clearing House,
  Clearing Member, Compression, Initial Margin, Position Netting, Variation
  Margin, and Warrant;
- Part 3, Regulations 6-10, covering prices and margin, the payment system,
  prompt dates, settlement, and delivery;
- Part 9, especially Regulations 1-3, covering events of default and default
  proceedings; and
- Part 10, especially Regulations 1, 3, 6, 8, 9, and 11, covering LMEsword's
  purpose, warrant creation and transfer, withdrawal, cancellation, and
  invalid warrants.

