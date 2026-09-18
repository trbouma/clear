# BIS Working Paper 1377 Hidden Complexity and Clear

Status: Analysis note

## Purpose

This note analyzes the Bank for International Settlements (BIS) Working Paper
No 1377, *Hidden by complexity? Measuring stablecoin, crypto and decentralised
finance ecosystems*, in relation to Clear.

The paper's central finding is directly relevant to Clear: public blockchain
data can be transparent at the technical record level while remaining ambiguous
at the economic-meaning level. The authors show that widely used indicators of
cryptoasset, stablecoin, and decentralised finance (DeFi) activity depend
heavily on methodological choices, technical classification, and assumptions
about what on-chain records mean.

Clear should treat this as both a warning and a positioning advantage. Clear is
not trying to infer economic meaning from a global programmable ledger after
the fact. It is designed to make issuer policy, Clear Mint Unit (CMU) identity,
treasurer authority, mint custody, and redemption meaning explicit before
Mint Notes circulate.

## Paper summary

The BIS paper examines measurement challenges in Bitcoin, Ethereum, Tron,
stablecoins, and DeFi. It argues that public-chain data is abundant but not
self-explanatory. On-chain indicators such as market capitalisation, transfer
volume, smart-contract activity, stablecoin supply, and total value locked can
look precise while concealing substantial methodological uncertainty.

The paper identifies three structural sources of measurement divergence:

1. **Aggregation challenge**: Bitcoin's unspent transaction output (UTXO)
   architecture makes it difficult to distinguish economically meaningful
   transfers from change outputs and self-transfers.
2. **Programmability challenge**: Ethereum-style smart contracts create large
   volumes of heterogeneous transactions, logs, traces, and state changes that
   are technically visible but difficult to classify economically.
3. **Comparability challenge**: the same stablecoin issued across different
   chains can serve different economic roles because infrastructure, fees,
   contract ecosystems, and user behaviour differ by chain.

The authors' policy conclusion is that on-chain indicators should be treated
as noisy approximations, not direct measures of economic activity. Effective
analysis requires bounded estimates, explicit assumptions, technical
classification, disaggregation, and expert judgment.

## Why this matters for Clear

Clear is being positioned against blockchains and stablecoins that often rely
on public ledger activity as evidence of use, liquidity, or systemic relevance.
The BIS paper weakens the simple claim that blockchain transparency equals
economic clarity.

For Clear, the point is not that public ledgers are useless. The point is that
technical records need institutional meaning. A transfer event, token symbol,
contract address, or stablecoin ticker is not enough to explain:

- who issued the unit;
- what obligation stands behind it;
- whether the holder can redeem it;
- what the unit is accepted for;
- whether activity represents payments, trading, collateral, liquidity
  provision, self-transfers, or noise;
- whether two apparently similar units are economically equivalent; or
- which actor is legally or operationally responsible.

Clear is designed to make those questions explicit at the minting layer:

```text
issuer policy
  -> treasurer authority
  -> keyset-bound CMU
  -> private bearer Mint Notes
  -> redemption, retirement, or reissue under policy
```

The BIS paper therefore supports one of Clear's core distinctions: Clear is not
just another payment rail. It is a minting and redemption system where economic
meaning is attached to the unit by policy, authority, and recognition rather
than inferred from a global smart-contract graph.

## Measurement opacity in public ledgers

The paper's main paradox is that blockchain data is public but difficult to
interpret. Public availability does not remove ambiguity.

### Bitcoin aggregation

Bitcoin's UTXO model stores value as discrete outputs. A transaction often
consumes whole outputs and returns change to the sender. Naively summing all
outputs can overstate economic transfer value because change outputs are
technical artifacts, not necessarily meaningful payments.

The paper reports that Bitcoin transfer values can vary by up to a factor of
six depending on methodology. It also shows that market capitalisation can
change substantially depending on how analysts treat lost coins, dormant coins,
and realised rather than spot valuation.

### Ethereum programmability

Ethereum's account-based smart-contract model creates a different measurement
problem. A single transaction can trigger many contract calls, logs, traces,
and state changes. Logs are useful but developer-defined and non-authoritative.
Traces and state diffs are more precise but complex to extract and interpret.

The paper finds massive smart-contract proliferation. It reports tens of
millions of deployed or active contracts, most of which remain outside simple
technical classification. It also finds roughly 1.4 million token-issuing
contracts and widespread reuse of symbols associated with major stablecoins.

### Stablecoin comparability

The same stablecoin can behave differently across chains. The paper's Tether
USD (USDT) analysis shows that USDT on Ethereum and USDT on Tron should not be
treated as one monolithic activity stream. Ethereum holdings are more closely
tied to DeFi intermediation, liquidity provision, and collateral activity,
while Tron activity appears more payment-like or store-of-value oriented.

The lesson is broader: same label, different infrastructure, different
economic meaning.

## Stablecoin symbol reuse and issuer ambiguity

One of the paper's most important findings for Clear is symbol reuse. The paper
identifies thousands of token contracts using symbols such as USDT, USD Coin
(USDC), and Dai (DAI) even though the authentic versions are issued from
specific contracts. It finds roughly 7,000 contracts using the USDT symbol and
notes that spurious activity rose with stablecoin growth.

This matters because stablecoin and token ecosystems often rely on names,
symbols, contract addresses, metadata, and off-chain knowledge to identify what
a token really is. The paper warns that name- and symbol-based metrics can
overstate economically meaningful assets and blur the boundary between real,
imitative, speculative, or malicious deployments.

Clear should draw a sharp product lesson:

```text
Display label is not identity.
CMU identity is exact: cmu-<keyset-id>.
Issuer policy gives the unit meaning.
```

Clear already avoids the ticker problem by treating the complete
`cmu-<keyset-id>` as canonical. A wallet may display a friendly name, but it
must preserve the exact CMU identity and issuer context. Two units that both
display "credits" or "CMU" are not interchangeable unless issuer policy says so
through an explicit migration, exchange, or recognition arrangement.

## Clear's explicit policy advantage

The BIS paper argues that technical classification must be combined with
economic analysis and off-chain linkage to legal entities. Clear can make that
linkage part of the unit lifecycle rather than a later analytics problem.

A Clear CMU should always make the following facts discoverable:

- issuer or policy domain;
- complete `cmu-<keyset-id>`;
- treasurer authority or policy version;
- issuing mint or mint cluster;
- redemption or retirement policy;
- keyset lifecycle state;
- acceptance and recognition context;
- supply-changing authorization evidence; and
- audit and spent-proof boundaries.

This does not eliminate trust. It makes the trust surface legible. A holder
still has to decide whether the issuer is credible, whether the redemption
policy is useful, and whether the mint is available. But the holder should not
have to infer the instrument's meaning from token names, event logs, DeFi
analytics, or chain-level activity metrics.

## Comparison with stablecoin measurement

The paper shows that stablecoin analysis has at least three ambiguity layers:

1. **Asset identity**: which contract or chain represents the relevant token?
2. **Use case**: is the token being used for payments, store of value, exchange
   custody, liquidity provision, collateral, bridging, or trading?
3. **Issuer linkage**: which legal or economic actor stands behind the token,
   and how does the on-chain instrument relate to off-chain reserves or
   obligations?

Clear should reduce those ambiguities at the design level:

| Measurement issue in stablecoin/DeFi ecosystems | Clear design response |
| --- | --- |
| Token symbols can be reused or imitated | Canonical identity is `cmu-<keyset-id>`, not symbol text |
| Same stablecoin differs by chain | A CMU is bound to one keyset and policy context; cross-route use does not erase identity |
| On-chain activity can mix payments, trading, collateral, and self-transfer noise | CMU purpose and redemption meaning are issuer-policy fields |
| Public logs may not map cleanly to economic meaning | Mint events should record authorization, issuance, redemption, retirement, and spent-proof evidence |
| Off-chain issuer linkage is hard to recover | Issuer and treasurer recognition should be explicit before circulation |
| Total value locked and transfer volume can be noisy | Clear should report bounded, policy-aware supply, redemption, and outstanding-note metrics |

## What Clear should not overclaim

The BIS paper is also a caution for Clear. Clear should not claim that a mint
ledger is automatically economically clear simply because it is narrower than a
blockchain.

Clear still needs disciplined metrics:

- issued supply by CMU;
- outstanding notes by CMU;
- redeemed and retired notes by policy reason;
- expired or suspended amounts;
- treasury-authorized issuance versus operational swaps;
- attempted double spends;
- mint availability and failed redemption attempts;
- migration between old and new CMUs;
- holder-facing acceptance context; and
- reserve, service, or inventory backing where policy requires it.

Clear metrics should be explicit about assumptions. For example, an outstanding
Mint Note is not automatically proof of active use. A redeemed note may
represent consumption, reimbursement, expiry, or administrative retirement
depending on policy. A high transfer count may indicate useful circulation or
automated churn. Clear should avoid recreating the same interpretive mistakes
that the paper identifies in DeFi analytics.

## Implications for Clear product design

The paper suggests several product and documentation requirements.

### Preserve exact CMU identity

Wallets and APIs must never treat friendly names, display symbols, issuer
logos, or unit aliases as canonical identity. The complete `cmu-<keyset-id>` is
the unit boundary.

### Make issuer policy machine-readable

A CMU should link to a policy document or policy descriptor that states what
the unit represents, who recognizes it, and how redemption or retirement works.

### Separate activity types

Clear analytics should distinguish issuance, wallet-to-wallet transfer,
refresh, swap, redemption, retirement, expiry, and migration. These are not one
generic "volume" metric.

### Avoid raw headline volume

Clear should not lead with unqualified transfer volume. It should report
policy-aware metrics such as issued, outstanding, redeemed, retired,
redemption-only, suspended, and expired amounts.

### Keep acceptance distinct from reachability

The paper's comparability lesson maps to Clear's acceptance model. A CMU may be
technically reachable across networks without being accepted by the recipient
or recognized by a community.

### Link technical state to institutional state

Clear's technical evidence should always point back to authority and policy:
which treasurer authorized issuance, which mint signed notes, which CMU was
affected, and what redemption policy applies.

## Implications for policy positioning

The paper gives Clear a strong policy message:

> Clear reduces ambiguity by making issuance authority, unit identity and
> redemption meaning explicit at the minting layer.

That message is different from saying Clear is simpler in every respect. Clear
has its own complexity: keyset lifecycle, treasurer governance, mint custody,
spent-proof state, wallet handling, acceptance policy, and redemption
operations. The difference is that Clear's complexity is organized around
issuer-defined instruments rather than around global smart-contract activity.

For policymakers, this creates a clearer supervision question:

```text
Who issued this CMU?
What does it represent?
Who may create or retire supply?
Where is spent-proof state maintained?
How is it redeemed?
Who recognizes it?
```

That is a more direct institutional frame than trying to infer economic
activity from token symbols, chain addresses, contract logs, bridge routes, and
aggregate stablecoin volumes.

## Risks and open questions

Clear should still answer:

- How does a wallet verify that a policy descriptor corresponds to the CMU it
  is displaying?
- How should Clear expose supply and redemption metrics without compromising
  holder privacy?
- What analytics should distinguish organic transfers from automated refresh
  or churn?
- How should CMU migration be reported so old and new keysets are not silently
  conflated?
- How should issuer legal identity be represented without forcing all use
  cases into the same regulatory template?
- How should closed-loop community credits disclose backing, acceptance and
  redemption limits?
- How should public-purpose issuers publish audit evidence without turning
  private Mint Notes into account-based surveillance?

These are solvable design questions, but they should be treated explicitly.

## Conclusion

The BIS paper supports Clear's critique of stablecoin and smart-contract
framing. Public blockchain records do not automatically provide clear measures
of economic activity. Names, symbols, logs, contract types and aggregate volume
can obscure more than they reveal.

Clear should respond by making the economic meaning of a unit explicit before
circulation:

```text
issuer policy + treasurer authority + cmu-<keyset-id> + mint spent-state
```

That does not make Clear trustless. It makes the relevant trust relationships
visible. Clear's opportunity is to provide minting infrastructure where private
bearer circulation is paired with explicit issuer responsibility, exact unit
identity and policy-aware redemption metrics.
