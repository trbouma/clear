---
title: Where Is the Holding?
description: Bitcoin outputs, Ethereum token contracts, and Cashu proofs distribute evidence, spending authority, privacy, and institutional dependence differently.
---

# Where Is the Holding?

The core distinctions are:

- **Bitcoin: ledger-enforced unspent outputs.**
- **Ethereum tokens: ledger-enforced contract balances.**
- **Cashu: mint-enforced unspent bearer proofs.**

Bitcoin tracks outputs, not whole unspent transactions. Native ETH uses account
balances; Ethereum tokens use contract balances. Cashu proofs live with the
holder, but their spendability depends on the mint's pending and spent state.
Ledger enforcement rests on network validation and consensus. None of these
mechanisms alone guarantees economic value or redemption.

Digital value is often discussed as though every system merely moves a balance
between wallets. A more revealing question is: **Where is the evidence of a
holding maintained, and who determines whether it can be spent?**

Bitcoin, Ethereum token contracts, and Cashu provide three different answers.
Clear builds on the third, but that does not make it independent of institutions.
It changes which institutions and records a holder relies on.

## Three models

| Dimension | Bitcoin | Ethereum ERC-20 tokens | Cashu |
| --- | --- | --- | --- |
| Holding evidence | Unspent transaction outputs (UTXOs) | Token contract state | Holder-held mint-signed proofs |
| Balance | Sum spendable outputs | Query the contract | Sum valid, unspent proofs |
| Transfer | Consume and create outputs | Execute a contract state change | Swap received proofs for fresh ones |
| Double-spend prevention | Network consensus | Consensus over contract execution | Mint's pending and spent state |
| Principal dependence | Protocol, consensus, and keys | Consensus, contract rules, and any administrators | Proof security, mint operation, and issuer obligations |

Bitcoin wallets calculate holdings from outputs with spending conditions;
these need not correspond to one public key. Nodes enforce validity rules and
consensus establishes the accepted history. [Bitcoin transaction guide](https://developer.bitcoin.org/devguide/transactions.html).

Ethereum records native ETH in account state. ERC-20 balances are maintained
separately by token contracts. An address is not necessarily an identified
person; contract accounts are governed by code. [Ethereum accounts](https://ethereum.org/en/developers/docs/accounts/).

ERC-20 standardizes an interface, not a complete monetary constitution.
Issuance, freezes, upgrades, and administrative powers vary by contract.
Faithful execution does not guarantee fair rules, freedom from defects, or
redeemable backing. [ERC-20 specification](https://eips.ethereum.org/EIPS/eip-20).

**Mainstream blockchain stablecoins generally use the balance-recording model
illustrated by Ethereum tokens**, rather than holder-held bearer proofs. This
does not mean they all run on Ethereum: ERC-20 is common on Ethereum-compatible
networks, while other blockchains use different token mechanisms. USDC, for
example, uses smart contracts on Ethereum-compatible chains and built-in token
primitives on other networks. The shared feature is ledger-maintained holdings,
not a single blockchain or token standard.
[Circle: Multichain USDC](https://www.circle.com/multi-chain-usdc).

A stablecoin's price target and backing are separate from this mechanism;
neither stable value nor redemption assurance follows from its accounting model.

Cashu places proof secrets and mint signatures with the holder. Blind signatures
support unlinkability between issuance and later spending; a named balance
account for every holder is not intrinsic to this model.
[Cashu NUT-00](https://cashubtc.github.io/nuts/00/).

## Possession is not settlement

Digital proofs can be copied. A recipient normally exchanges incoming proofs
at the mint for fresh proofs with secrets unknown to the sender. Successful
input invalidation prevents the sender from reusing the old proofs, assuming
correct mint operation. Merely receiving the data is insufficient.
[Cashu NUT-03](https://cashubtc.github.io/nuts/03/).

Four questions must remain separate:

- **Possession:** Does the holder have the proof material?
- **Authenticity:** Is it genuinely signed for the stated mint parameters?
- **Unspent status:** Has the mint already accepted it or reserved it in an ongoing operation?
- **Redeemability:** Can and will the responsible institution honor its terms?

A status check is not a reservation or an authenticity test. In particular,
`UNSPENT` means the mint has no pending or spent record; it is not a guarantee
that a later spend will succeed. [Cashu NUT-07](https://cashubtc.github.io/nuts/07/).

Ordinary Cashu therefore does not offer final offline settlement. Offline
acceptance involves risk, even when the proof data looks correct.

## Policy consequences

**Privacy and accountability are different design questions.** Public ledger
addresses can reveal relationships without containing names. Cashu can avoid
routine holder balance accounts, but timing, amounts, network data, and
redemption records can weaken practical privacy. Issuance accountability need
not require a complete history of everyone's purchases.

**Administrative control must be inspected, not inferred.** Some token
contracts have powerful administrators; others do not. A mint can refuse
service even when it cannot identify every holder. Privacy does not eliminate
censorship risk, and distributed execution does not eliminate issuer discretion.

**Outages have different remedies.** Changing a blockchain data provider can
restore access to a functioning network. It cannot repair a paused contract.
A failed mint can leave holders with intact proof files but no normal way to
complete safe receipt or redemption. Mint restoration must preserve spent
state, not just signing keys.

**Recovery has a price.** Backups help with some losses, not value already
spent by a thief. Identity-based recovery, custody, and additional authorization
rules change the product's privacy and control properties. Commercial disputes
also need procedures beyond showing that a technical transfer succeeded.

**Backing is not an accounting property.** Native BTC and ETH are not ordinarily
issuer redemption claims. Tokens and proofs can represent such claims, but
their meaning depends on actual obligations. A valid balance or signature
cannot establish reserve availability or issuer solvency.

**Audit should target obligations, not unnecessary surveillance.** Aggregate
issuance, outstanding liabilities, redemption performance, reserve definitions,
and independent controls can inform holders without publishing their activity.
Self-reported totals do not prove that unauthorized issuance never occurred.

## What this means for Clear

Clear uses Cashu mechanisms while decoupling treasury-authorized issuance from
a mandatory Bitcoin and Lightning funding model. Each Clear Mint Unit (CMU)
needs an explicit issuer, authority structure, economic meaning, and redemption
policy. Sharing a mint does not make different units interchangeable or jointly
guaranteed.

For communities and corporations, this could support circulating service,
resource, or purchasing entitlements without a treasury account for every
holder. For a larger public payment system, the same model would require much
stronger continuity, inclusion, independent assurance, and loss-allocation
arrangements. Cryptography does not supply those institutional safeguards.

Clear should distinguish receipt from successful swap in its user experience,
publish unit-specific obligations, test operational recovery, and minimize
unnecessary metadata collection. These are evaluation priorities, not a claim
that all production safeguards already exist.

**The policy conclusion is not that one architecture removes trust. It is that
each places trust differently.** Decentralization, privacy, possession, and
redemption assurance should be assessed separately.

## Further reading

[Detailed analysis: Holding Evidence and Spending Authority](https://github.com/trbouma/clear/blob/main/docs/HOLDING-EVIDENCE-AND-SPENDING-AUTHORITY.md)

[Cashu, Decoupled](cashu-decoupled.md) explains Clear's treasury model.
[Clear Is Not a Stablecoin](chaumian-mint-vs-stablecoins.md) examines the narrower
comparison with issuer-backed smart-contract schemes.
