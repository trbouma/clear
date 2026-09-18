---
title: Hidden Complexity and Clear
description: What stablecoin and decentralised finance measurement research says about Clear's minting model.
---

# Hidden Complexity and Clear

A recent Bank for International Settlements (BIS) working paper makes a point
that matters for Clear: public blockchain data can be technically transparent
without being economically clear.

The paper, *Hidden by complexity? Measuring stablecoin, crypto and
decentralised finance ecosystems*, studies Bitcoin, Ethereum, Tron,
stablecoins, and decentralised finance (DeFi). Its core finding is that
headline indicators such as transfer volume, market capitalisation,
stablecoin activity, and total value locked depend heavily on methodology and
technical assumptions.

That finding reinforces a central Clear argument. A digital unit should not
rely on after-the-fact interpretation of chain activity to explain what it is.
The issuer, unit identity, authority and redemption policy should be explicit
before the unit circulates.

## Transparency is not the same as meaning

Public blockchains record enormous amounts of data. That does not mean the
economic meaning of the data is obvious.

The paper identifies three recurring measurement problems:

- Bitcoin-style transaction outputs make it hard to separate real economic
  transfers from technical change outputs.
- Smart contracts create large volumes of logs, traces, events and state
  changes that are visible but difficult to classify.
- The same stablecoin can behave differently across chains because each chain's
  fees, architecture and user base shape use.

The result is a paradox. More public data does not automatically mean more
clarity. Without technical classification and explicit assumptions, public
ledger metrics can become noisy approximations.

## Stablecoin labels can mislead

One of the paper's most important findings is symbol reuse. It identifies
thousands of token contracts using labels such as Tether USD (USDT), USD Coin
(USDC) and Dai (DAI) even though the authentic versions are issued from
specific contracts.

That matters because a token symbol is not an issuer. A ticker is not a policy.
A contract label is not proof of economic meaning.

Clear is designed to avoid that ambiguity. A Clear Mint Unit (CMU) is identified
by its complete `cmu-<keyset-id>`, not by a friendly label. A wallet may display
a useful name, but the protocol identity remains exact.

```text
Display label: community credits
Canonical identity: cmu-<keyset-id>
Issuer meaning: defined by policy
```

Two units can both display "credits" or "CMU" and still represent completely
different obligations. They become interchangeable only if an issuer policy
explicitly makes them so.

## The same asset can mean different things

The paper shows that USDT on Ethereum and USDT on Tron should not be treated as
one simple activity stream. On Ethereum, USDT is more closely tied to
decentralised finance activity such as liquidity provision and collateral. On
Tron, USDT appears more payment-like or store-of-value oriented.

The lesson for Clear is simple: infrastructure changes meaning.

Clear should therefore keep the full context of every unit visible:

- issuer or policy domain;
- complete CMU identity;
- treasurer authority;
- issuing mint or mint cluster;
- redemption or retirement policy;
- keyset lifecycle state; and
- acceptance context.

The same mint may support many treasury units, but they should not collapse
into one balance or one headline metric.

## Clear makes policy part of the unit

Stablecoin and DeFi analytics often try to recover meaning from addresses,
contracts, logs, token labels and transaction graphs. Clear should reverse that
order.

```text
issuer policy
  -> treasurer authority
  -> keyset-bound CMU
  -> private bearer Mint Notes
  -> redemption or retirement under policy
```

The policy comes first. It says what the unit represents, who may issue it,
where it is recognized, and what happens when Mint Notes are redeemed.

The minting mechanism then gives that policy a private bearer form. Holders
carry Mint Notes. The mint checks spent-proof state. Redemption or retirement
closes the loop.

## Clear still needs careful metrics

The paper is also a warning for Clear. A narrower mint ledger is not
automatically meaningful. Clear should avoid vague volume metrics and report
policy-aware activity instead.

Useful Clear metrics should distinguish:

- issued supply;
- outstanding notes;
- redeemed notes;
- retired notes;
- expired amounts;
- suspended or redemption-only CMUs;
- treasury-authorized issuance;
- operational swaps and refreshes; and
- attempted double spends.

A transfer count is not enough. A high amount outstanding may represent useful
circulation, dormant balances, unreconciled redemption, or future service
claims. The issuer's policy gives those numbers meaning.

## Why this matters for policy makers

The BIS paper concludes that on-chain indicators should be treated as noisy
approximations rather than direct measures of economic activity. Clear accepts
that lesson and builds around it.

The relevant questions for a Clear unit are not:

```text
What ticker does this resemble?
How much volume did a public chain report?
Which token label appears in the logs?
```

The relevant questions are:

```text
Who issued this CMU?
What does it represent?
Who may create or retire supply?
Where is spent-proof state maintained?
How is it redeemed?
Who recognizes it?
```

Those are minting questions. Clear's contribution is to make them explicit in
the design of the unit rather than asking analysts to reconstruct them from
blockchain activity later.

## The policy takeaway

Clear should be understood as a response to hidden complexity, not as another
layer of it.

It does not claim that software eliminates trust. It makes trust relationships
legible:

```text
issuer policy + treasurer authority + cmu-<keyset-id> + mint spent-state
```

That is different from a stablecoin ecosystem where technical transparency can
still leave economic meaning, issuer linkage and use case unclear.

For the detailed technical analysis, see
[BIS WP 1377 Hidden Complexity and Clear](https://github.com/trbouma/clear/blob/main/docs/BIS-WP1377-HIDDEN-COMPLEXITY-CLEAR-ANALYSIS.md).
