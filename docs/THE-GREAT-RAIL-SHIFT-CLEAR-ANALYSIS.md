# The Great Rail Shift and Clear

Status: Analysis note

## Purpose and scope

This note analyzes *The Great Rail Shift: Convergence between Legacy
Infrastructure and Stablecoin Rails* in relation to Clear.

The report argues that stablecoins will not simply replace banks or legacy
payment systems. Instead, blockchains, stablecoins, tokenized deposits,
liquidity providers, banks, custodians, and clearing mechanisms will converge
into a layered hybrid architecture. It focuses on cross-border business
payments, foreign exchange, treasury management, trade, yield, geographic
dollarization, bank participation, and agentic payments.

That thesis is highly relevant to Clear, but the relationship is not that Clear
should become another stablecoin rail. The report largely begins with existing
money and asks how it can move more efficiently. Clear begins one institutional
step earlier:

```text
Who defines the unit?
Who may issue it?
What obligation or entitlement does it represent?
Who recognizes it?
What does redemption accomplish?
```

Clear then uses the Cashu protocol to give that answer a private bearer form.

This note treats the report as an industry-positioning document rather than an
independent empirical study. Its quantitative claims, projections, and
interview statements are useful signals, but the document provides limited
source notes and methodology for independently reproducing many of them.

## Executive finding

The report supports three important conclusions for Clear.

First, **payment rails are becoming modular and interchangeable**. Banks,
stablecoins, tokenized deposits, market makers, and clearing venues may all
participate in one transaction. Clear should remain rail-agnostic and treat
these systems as optional funding, exchange, and settlement adapters.

Second, **rules, authority, liquidity, and redemption matter more than token
issuance alone**. The report repeatedly shows that issuing a token does not
create its market, establish its liquidity, or make counterparties trust it.
That reinforces Clear's policy-first model.

Third, **the next problem is not merely movement but controlled delegation**.
The report's discussion of agentic payments, on-behalf-of authority, verifiable
intent, and limited blast radius aligns closely with Clear's treasurer grants
and bounded Mint Notes. Clear can fund an agent with a bearer allowance without
giving it an open-ended bank or stablecoin credential.

The central distinction is:

> Stablecoin convergence is a rail shift. Clear is a unit-and-authority shift
> that can use those rails without being defined by them.

## The report's argument

### Legacy infrastructure remains formidable

The report does not portray existing financial infrastructure as obsolete. It
highlights the network effects, regulatory clarity, counterparty trust,
privacy, security, revocability, sanctions screening, and liquidity of
established bank systems. It also points to the enormous daily values processed
by high-value payment systems.

Its criticism is narrower: cross-border payments still require fragmented
correspondent relationships, prefunded nostro and vostro balances, foreign
exchange operations, compliance coordination, and trapped liquidity. These
costs are especially visible in weaker corridors and emerging markets.

### Stablecoins serve as an intermediate rail

The report presents stablecoins as a way to compress settlement time, broaden
access to dollar liquidity, reduce correspondent hops, and aggregate liquidity
across banks, market makers, centralized venues, and decentralized venues.

The stablecoin is frequently temporary:

```text
local fiat
  -> stablecoin or tokenized deposit
  -> cross-border transfer or onchain FX
  -> destination stablecoin or fiat
```

In this model, the token is an intermediate settlement asset rather than the
ultimate economic object.

### Liquidity and distribution determine usefulness

The report stresses that token issuance is not market creation. Competitive
pricing depends on corridor-specific liquidity, provider depth, issuer access,
market-making capacity, distribution, and reliable off-ramps.

This is an important correction to infrastructure-first thinking. A digital
instrument does not become useful merely because it is technically
transferable. Counterparties must recognize it, liquidity providers must price
it, and redemption must be reliable.

### Banks and clearing mechanisms reappear

The report anticipates a hybrid system rather than a purely decentralized
endpoint. Banks may issue tokenized deposits, custody stablecoin reserves,
provide regulated settlement endpoints, and participate in clearing layers
that exchange same-peg instruments at par.

It uses “clearing” primarily in the sense of interoperability and guaranteed
conversion among stablecoins and bank money. That is narrower than the full
institutional meaning of clearing, which can also encompass acceptance,
novation, netting, margin, default management, and delivery. Clear should not
adopt the broader clearing-house label merely because it can issue or redeem a
settlement instrument.

### Agentic payments require delegated authority

The report argues that high-value agent payments need more than programmable
money. They require governance, legal framing, identity propagation, delegated
scope, auditability, permission controls, and a separation between intent and
execution.

This is one of its strongest observations. An agent needs not only a rail, but
an answer to:

```text
Who is the principal?
What may the agent do?
For how much?
For how long?
For what purpose?
Who is liable?
What evidence proves the action was authorized?
```

## Where Clear agrees

### Moving value is not the unsolved problem

The report includes the observation that moving money is largely solved while
enterprise configuration of movement rules is not. Clear reaches the same
conclusion from a different direction.

Blockchains, bank networks, card systems, real-time payment systems, Bitcoin,
and Lightning can all move established units. Clear addresses the prior
institutional problem: creating a precise circulating unit under delegated
authority.

```text
Payment rail question:
How does an existing unit reach the recipient?

Clear question:
What unit may this institution issue, under whose authority, and with what
redemption promise?
```

### Hybrid architecture is likely

Clear should not require one universal settlement network. A Clear Mint Unit
(CMU) can coexist with:

- bank deposits used to fund issuance;
- stablecoins used to reimburse providers;
- Bitcoin or Lightning balances in the same wallet;
- foreign exchange venues used for conversion;
- warehouse systems used to release goods;
- enterprise resource planning systems used for accounting; and
- government or organizational systems used to determine eligibility.

The mint should preserve a narrow responsibility: authority verification,
Cashu signing, bearer-proof validation, swaps, spent state, and policy-aware
supply evidence.

### Issuance is not adoption

Clear's ability to create a CMU does not create demand or acceptance. Each
issuer must establish a community of recognition:

- recipients willing to hold the unit;
- providers willing to accept it;
- redemption agents willing and able to perform;
- exchanges or conversion arrangements where needed; and
- policy credibility sufficient for holders to bear issuer risk.

The report's liquidity analysis therefore maps to Clear as an **acceptance and
redemption problem**, not only a market-making problem.

### Treasury is a central use case

The report finds strong stablecoin use in treasury movement, supplier
settlement, capital calls, drawdowns, distributions, import-export, and
repatriation. Clear is also treasury infrastructure, but it changes the object
the treasury can manage.

Stablecoin treasury systems optimize movement of externally defined money.
Clear allows a treasury to create purpose-specific bearer units representing
an allocation, liability, entitlement, service capacity, or warehouse claim.

These models can compose:

```text
ordinary money or stablecoin funds a program
  -> treasurer authorizes purpose-specific CMU issuance
  -> Mint Notes circulate privately
  -> provider redeems Mint Notes
  -> provider receives stablecoin, bank payment, goods, or accounting credit
```

## Where Clear differs

### Clear is not a stablecoin

A stablecoin typically presents a familiar monetary unit on a blockchain and
promises conversion at or near par. Clear makes no universal par claim.

Every CMU is a separate issuer-defined instrument identified by its complete
`cmu-<keyset-id>`. Two CMUs with similar display names remain different unless
an explicit policy or exchange mechanism relates them.

This is the opposite of the report's same-peg “singleness of money” objective.
Stablecoin clearing seeks to make multiple representations of one currency
behave as one. Clear's primary safety rule is to keep different institutional
promises separate.

### Clear decouples Cashu from a fixed settlement rail

Most Cashu mints issue sat-denominated ecash after receiving Bitcoin or
Lightning payment and redeem ecash through an outgoing payment. Clear retains
Cashu's bearer-note protocol but replaces payment-triggered issuance with
signed treasury authorization and policy-defined redemption.

```text
Typical payment-backed ecash:
payment -> private bearer notes -> payment

Clear:
policy -> treasury authority -> private bearer notes -> policy consequence
```

Stablecoins and banks can appear at either edge, but they do not have to define
the CMU.

### Privacy is architectural, not merely institutional

The report lists privacy among the strengths of legacy infrastructure but
focuses stablecoin design on compliance, screening, custody, and transparent
onchain settlement.

Clear uses blind signatures so the mint need not link note issuance with later
proof presentation. Holders carry Mint Notes rather than named balances at the
mint. This creates a different privacy boundary.

It does not eliminate compliance. A program can enforce eligibility at
issuance and required controls at redemption. Wallet, network, timing,
denomination, and endpoint metadata can still reveal information. The point is
that intermediate transfers need not automatically become a public transaction
graph or a complete issuer-held account history.

### Clear starts with plural units

The report anticipates multi-currency and multi-issuer infrastructure but
continues to value convergence, interoperability, and par exchange.

Clear assumes plurality is often legitimate:

- one food program is not another food program;
- one warehouse grade is not another grade;
- one crop year is not another year;
- one issuer's compute credit is not another issuer's credit; and
- one community's promise is not another community's liability.

Interoperability must preserve identity. Conversion should be an explicit
transaction, not accidental balance aggregation.

## Implications for Clear architecture

### A layered model

The report's convergence thesis suggests a five-layer Clear architecture:

```text
1. Institutional policy and authority
   root authority, treasurer scope, CMU policy, limits

2. Bearer instrument
   Cashu keysets, Mint Notes, swaps, spent-proof state

3. Acceptance and redemption
   merchants, providers, warehouses, compute services, program agents

4. Funding and settlement adapters
   banks, stablecoins, Bitcoin, Lightning, internal ledgers, goods delivery

5. Exchange and clearing
   quotes, conversion, liquidity, netting, reconciliation, default rules
```

Clear currently concentrates on layers one and two and provides the basic
boundary into layer three. It should integrate with the remaining layers rather
than silently absorbing their responsibilities.

### Rail-agnostic redemption adapters

A CMU policy should identify permitted redemption consequences and the adapter
responsible for each one. Examples include:

| CMU | Redemption adapter |
| --- | --- |
| Supplier credit | Bank or regulated stablecoin payment |
| Community voucher | Provider reimbursement system |
| Compute credit | Metering and service-control system |
| Clear Warehouse Unit | Warehouse registry and delivery process |
| Internal corporate unit | Enterprise resource planning or accounting system |

The mint receipt proves that valid notes were accepted. The adapter proves or
records the external performance. Those are related but distinct events.

### Exchange without identity collapse

Future Clear exchange services may quote one CMU against another or against
money. They should never imply automatic par conversion simply because units
share a label.

Every quote should identify:

- source and destination CMUs;
- exact issuer and mint boundaries;
- price, spread, fees, and expiry;
- liquidity provider or conversion authority;
- settlement consequence; and
- failure and refund treatment.

This applies the report's corridor-by-corridor liquidity lesson to Clear.

### Policy-aware treasury metrics

The report warns indirectly that gross stablecoin volume is dominated by
trading, liquidity provision, and internal rebalancing. Clear should avoid the
same mistake.

Metrics should distinguish:

- treasury-authorized issuance;
- outstanding supply;
- operational swaps;
- holder redemption;
- administrative retirement;
- conversion between CMUs;
- external settlement completed;
- settlement pending or failed; and
- backing, inventory, budget, or service capacity where applicable.

A high transfer or swap volume is not automatically evidence of useful
economic activity.

## Implications for agentic payments

### Funded authority rather than an open credential

The report focuses on agents carrying delegated identity and authority through
payment systems. Clear offers a complementary model: give the agent a bounded
bearer allowance.

```text
principal establishes policy
  -> treasurer funds agent with 1,000 compute CMU
  -> agent delegates or spends Mint Notes
  -> service redeems notes as work is performed
  -> no agent can spend more than the notes it controls
```

This limits the blast radius without requiring every service to receive the
principal's reusable payment credential.

### Identity delegation and value delegation are different

On-behalf-of frameworks answer who the agent represents and what it may request.
Mint Notes answer what bounded value the agent currently controls.

They can be combined:

```text
delegated identity and intent
  + bounded CMU allowance
  + service-specific acceptance policy
  + signed redemption evidence
```

Clear should not force identity into every bearer transfer. Instead, policy can
require identity or verifiable intent at selected issuance, service, or
redemption boundaries.

### Authorization and capture

The report's comparison with card authorization and capture is useful for
Clear. A future conditional-spend design could separate:

1. **allocation**: the agent receives or locks a bounded amount;
2. **authorization**: policy permits a defined service action;
3. **capture**: the provider receives spendable Mint Notes when conditions are
   satisfied; and
4. **retirement or settlement**: the provider redeems the notes.

This should build on proven Cashu spending conditions or escrow mechanisms,
not on ambiguous application promises.

## Implications for commodity trade

The report identifies settlement, foreign exchange, letters of credit,
compliance, and correspondent banking as major friction points in physical
commodity trade. Stablecoins may improve the cash leg.

Clear Warehouse Units could address a different leg: the privately circulating
entitlement to standardized inventory.

```text
Cash or stablecoin leg             Commodity entitlement leg
----------------------             -------------------------
bank or stablecoin rail     <->    Clear Warehouse Unit
FX and liquidity provider          warehouse and registry
cash settlement                    delivery or warrant redemption
```

Clear should not claim atomic delivery-versus-payment until a defined
orchestration mechanism coordinates both legs and handles partial failure.

## Risks and limitations in applying the report

### Industry perspective

The report is closely aligned with Delos Financial's product thesis and relies
substantially on statements from market participants. This gives it practical
signal but also creates selection and commercial-positioning bias.

### Measurement uncertainty

Headline stablecoin volume can mix payments, trading, market making,
rebalancing, and automated activity. The report acknowledges this, but many of
its market estimates and forecasts are not accompanied in the document by
enough methodology to reproduce them.

### Atomicity can be overstated

A blockchain transfer may be technically atomic while the whole transaction
is not. Foreign exchange, compliance approval, banking access, off-ramp
liquidity, goods delivery, and legal discharge may remain asynchronous and
revocable.

### Stablecoin access can shift rather than remove trust

Stablecoins can reduce correspondent hops while introducing issuer, reserve,
custodian, smart-contract, chain, bridge, wallet, and off-ramp dependencies.
The report recognizes the importance of regulated endpoints but generally
emphasizes opportunity over failure modes.

### Dollarization is a policy tradeoff

Improved access to dollar-linked settlement can support trade while weakening
local monetary sovereignty or local bank funding. Clear's plural-unit model
could support local and purpose-specific instruments, but it cannot remove the
economic reasons users prefer a more liquid external currency.

## Recommendations

1. Position Clear as **unit and authority infrastructure that composes with
   converging rails**, not as another universal rail.
2. Keep Bitcoin, Lightning, stablecoin, bank, commodity, and internal-ledger
   integrations behind explicit funding and redemption adapters.
3. Add machine-readable CMU fields for redemption consequence, settlement
   adapter, finality rule, issuer, policy version, and dispute channel.
4. Distinguish proof acceptance, note retirement, external settlement, and
   obligation discharge in APIs and metrics.
5. Design agent funding around bounded Mint Note possession plus optional
   delegated identity and verifiable intent.
6. Build CMU exchange as explicit corridor-specific quoting, never as implicit
   equivalence between similarly named units.
7. Preserve private intermediate transfers while locating required compliance
   controls deliberately at issuance, exchange, service, and redemption edges.
8. Treat liquidity, distribution, acceptance, and redemption capacity as
   product requirements for each CMU, not consequences of issuance.

## Conclusion

*The Great Rail Shift* argues that stablecoins will become an intermediate
settlement layer connecting compliant bank endpoints inside a hybrid financial
architecture. That is plausible, and Clear should be able to use such an
architecture.

Clear's deeper contribution is to make the bearer instrument independent of
any one rail. Cashu supplies private digital notes. Treasury policy supplies
authority and meaning. Banks, stablecoins, Bitcoin, Lightning, warehouses, and
enterprise systems can fund or settle the resulting unit without becoming the
institution that defines it.

The report describes convergence among ways of moving existing money. Clear
opens a complementary frontier: precise issuer-defined units that can move
across those converging systems while preserving their own authority,
identity, privacy, and redemption terms.

The strongest positioning is therefore:

> The rail shift makes value movement modular. Clear makes the unit itself
> institutionally programmable without making its holders live on an account
> ledger or public blockchain.

## Source

This analysis is based on [The Great Rail Shift: Convergence between Legacy
Infrastructure and Stablecoin Rails (source PDF)](../website/assets/sources/The-Great-Rail-Shift.pdf),
a 32-page report dated September 2026. The original PDF is preserved in this
repository.
