# Holding Evidence and Spending Authority

Status: Analysis note

## Purpose and scope

**Where is the evidence of a holding maintained, and who determines whether it can be spent?**

This question distinguishes three architectures that are often grouped together as digital money: Bitcoin unspent transaction outputs (UTXOs), Ethereum ERC-20 token contracts, and Cashu bearer proofs. Their differences concern not just transaction speed or cost, but the distribution of recordkeeping, visibility, authority, and institutional dependence.

The comparison addresses base-layer Bitcoin, Ethereum execution of ordinary ERC-20 contracts, and the ordinary Cashu bearer-proof workflow. Custodial wallets, additional spending conditions, privacy systems, bridges, and secondary networks can change the analysis. Recommendations for Clear below are design and governance recommendations, not claims that every safeguard is implemented.

The core conclusion is that **decentralization, privacy, possession, and redemption assurance are independent dimensions**. A public ledger can be decentralized yet highly observable. A private bearer instrument can depend on a single operator. A perfectly recorded holding can represent an insolvent issuer's promise.

## 1. The comparison

| Dimension | Bitcoin | Ethereum ERC-20 tokens | Cashu |
| --- | --- | --- | --- |
| Representation | Unspent outputs with spending conditions | Balances maintained by a token contract | Mint-signed proofs held by the holder |
| Balance calculation | Sum outputs the wallet can spend | Query the contract's balance interface | Sum authentic, unspent, spendable proofs of the same unit |
| Transfer | Consume outputs and create new outputs | Execute code that changes contract state | Recipient exchanges received proofs for fresh proofs at the mint |
| Double-spend control | Consensus over transaction history and the UTXO set | Consensus over execution and resulting state | Mint enforcement of pending and spent state |
| Holder's essential capability | Satisfy output spending conditions | Obtain an authorized state transition under contract rules | Present eligible proofs and obtain mint acceptance |
| Principal dependencies | Protocol rules, consensus, keys, transaction inclusion | Ethereum consensus, contract logic, any administrators, keys | Proof secrecy, mint integrity and availability, issuer obligations |
| Economic character | Native BTC, not ordinarily an issuer redemption claim | Whatever the particular token represents | Whatever the particular mint and unit promise |

No row establishes which asset is money, legal tender, a deposit, a security, or a warehouse entitlement. Those questions require the actual instrument's terms and applicable law.

## 2. Bitcoin: evidence in a shared output history

Bitcoin has no conventional balance account for each holder. A wallet identifies outputs whose conditions it can satisfy and sums their value. A transaction spends previous outputs and creates new ones. Conditions can involve signatures, multiple parties, time restrictions, or scripts rather than a single public key. Nodes independently validate transactions; consensus determines the accepted history. [Bitcoin Developer Guide: Transactions](https://developer.bitcoin.org/devguide/transactions.html).

For policy purposes, the holder has an authorization capability, not a file that independently establishes a current holding. A private key can remain unchanged after the associated output has been spent. Conversely, an output remains recorded even when nobody can satisfy its spending conditions because keys have been lost.

This separates **control of credentials** from **existence of spendable value**. Independent validation reduces reliance on a particular service provider, but does not remove the need for the network to include a transaction. A valid transaction is not necessarily promptly confirmed. Confirmation also carries reorganization risk rather than an absolute promise by an institution.

Native BTC should not be evaluated as though a treasury owes each holder redemption at par. Its exchange value is a different question from the validity of its outputs. A wrapped bitcoin token or custodial bitcoin account introduces additional obligations absent from native output ownership.

## 3. Ethereum: evidence in executable account state

Ethereum maintains native ETH balances in account state. Externally owned accounts ordinarily use private-key authorization; contract accounts operate through code. An address identifies an account, not necessarily a named person or a single human-controlled key. ERC-20 holdings are separate from native ETH balances and are maintained by individual token contracts. [Ethereum documentation: Accounts](https://ethereum.org/en/developers/docs/accounts/).

ERC-20 defines an interface for balances, transfers, supply, and allowances. It does not prescribe all internal bookkeeping, issuance policy, freezing powers, or upgrade governance. Compliance with that interface therefore does not imply uniform trust requirements. [ERC-20 specification](https://eips.ethereum.org/EIPS/eip-20).

The crucial policy distinction is between **execution assurance** and **substantive assurance**. Ethereum can faithfully execute a token's rules even when those rules permit an administrator to block transfers or increase supply. It can faithfully execute a defect. It cannot establish that an external reserve exists merely because a contract reports a balance.

Assessment must therefore examine the deployed contract, proxy and upgrade arrangements, role assignments, and external dependencies. Administrative powers are neither universal to ERC-20 nor ruled out by it. An immutable contract and an upgradeable issuer-controlled token can expose the same standard interface while offering different protections.

Allowances introduce a further authorization boundary: another contract may be permitted to spend tokens. Wallet compromise is not the only route to loss; an unsafe approval can expose value while the account's private key remains secret.

## 4. Cashu: holder-held evidence, mint-maintained exclusion

Cashu proofs contain secrets and mint signatures associated with denominations and keysets. Blind issuance separates the message signed during issuance from the proof later presented. The basic model does not require a balance account for every holder. The mint nevertheless remains an active service, not simply a passive signature verifier. [Cashu NUT-00](https://cashubtc.github.io/nuts/00/).

On receipt, a wallet normally swaps incoming proofs: the mint invalidates accepted inputs and returns blinded signatures for new outputs chosen by the recipient. The recipient obtains fresh secrets unknown to the sender. [Cashu NUT-03](https://cashubtc.github.io/nuts/03/).

Cashu consequently divides the recordkeeping problem. The wallet holds positive evidence of a claim; the mint maintains authoritative exclusion state needed to reject reuse. It also needs operational records for issuance, swaps, redemption, and recovery. Removing holder balance accounts does not remove databases, consistency requirements, or institutional control.

### Four distinct questions

| Question | What it establishes | What it does not establish |
| --- | --- | --- |
| Possession | Someone has the proof material and any required authorization | Exclusive possession; a sender or thief may retain a copy |
| Authenticity | The proof corresponds to a valid mint signature for its stated parameters | That it remains unspent or has economic backing |
| Unspent status | The mint has not recorded it as pending or spent at the time checked | Authenticity, a reservation, or success in a later race |
| Redeemability | The issuer can and will honor the applicable entitlement under its terms | Established merely by any cryptographic check |

NUT-07 reports `UNSPENT`, `PENDING`, or `SPENT`; `UNSPENT` means no pending or spent record is known. The status check does not itself validate a signature. An unknown identifier can have no spent record without corresponding to a genuine proof. [Cashu NUT-07](https://cashubtc.github.io/nuts/07/).

Authenticity must be established through the mint's validation or an appropriate supported verification mechanism. The baseline signature format should not be described as universally verifiable offline merely from possession of a public key.

### The receipt race

Consider a merchant who receives a copied proof while the sender retains it. A status response is only a snapshot; it does not reserve value for the merchant. Acceptance requires a successful swap with consistently enforced input invalidation. If the sender spends first, the merchant's later attempt can fail. A successful swap protects against reuse of those old inputs, assuming correct mint operation, but does not eliminate issuer default risk.

An offline handoff can therefore transfer data and a contingent claim, not provide ordinary Cashu final offline settlement. Offline acceptance is a credit or fraud-risk decision unless a separate mechanism supplies additional guarantees.

## 5. Privacy and identifiable accounts

Bitcoin and ordinary Ethereum token activity expose transaction relationships on public ledgers. Addresses are not inherently civil identities, but reuse, counterparties, and service records can connect them to people. Account-based does not necessarily mean named-account-based, and output-based does not necessarily mean private.

Cashu need not maintain a running balance by person or address. This can reduce the collection of transaction histories as a condition of everyday circulation. Cryptographic unlinkability does not mean the mint sees nothing: request timing, amounts, network identifiers, authentication, and issuance or redemption records may reveal associations. Wallet telemetry can undermine privacy independently of mint behavior.

For Clear, a useful policy objective is to separate accountability for treasury issuance from unnecessary identification of every subsequent holder. Whether identification is required at any boundary depends on the activity and jurisdiction; privacy architecture does not settle compliance obligations. Data minimization should be designed and reviewed rather than presumed from blind signatures.

## 6. Discretion, censorship, and rule changes

All three models have potential exclusion points, but at different layers. A blockchain service can refuse access while other providers remain available. Network-level transaction exclusion is a different problem. A token administrator may have powers under the contract that no alternative service provider can bypass.

A Cashu mint can refuse requests or become unavailable. Blindness may limit its ability to identify a particular holder or reconstruct circulation, but does not prevent service-wide suspension, discriminatory access policies, or refusal at identified redemption boundaries. A mint's operational authority and an issuer's legal obligations must be assessed separately.

Clear should disclose who can authorize issuance, operate signing services, change acceptance policy, and honor redemption. Treasury authority does not automatically mean personal custody of mint signing secrets. Changes should state how existing notes are treated, not merely how future issuance changes. Private bearer circulation makes arbitrary retrospective recovery difficult; it should not be marketed as an ordinary account reversal facility.

## 7. Resilience and unavailable services

| Failure | Practical consequence | Appropriate response |
| --- | --- | --- |
| Wallet's blockchain data provider fails | Access or visibility can fail despite a functioning network | Alternative providers or independently operated nodes |
| Blockchain stops progressing | New transfers cannot reach normal confirmation or finality | Network recovery and explicit pending-payment rules |
| Token contract pauses or has a defect | Token transfer can fail while Ethereum continues operating | Contract-specific governance and incident procedures |
| Cashu mint fails | Proof files survive, but normal safe receipt and redemption can stop | Tested mint restoration, continuity arrangements, clear liability allocation |
| Issuer or redemption custodian defaults | Technically valid instruments may lose their promised economic utility | Reserve governance, enforceable claims, orderly resolution |

Replicating mint servers is insufficient if replicas disagree about spent proofs. Recovery must preserve authoritative spent state and prevent stale databases from accepting previously consumed inputs. Signing-key backups without transaction-state recovery are not a complete continuity plan.

Multiple mints can diversify exposure but do not automatically accept each other's proofs. Cross-mint interchange requires liquidity, acceptance arrangements, and settlement rules. Shared software is not shared liability.

## 8. Loss, theft, recovery, and disputes

Loss of keys or proof secrets can remove access even when the underlying records or obligations remain. Backups can address some accidental losses; they do not undo theft. Restoring a copy of bearer material cannot recreate value already spent by an attacker.

Recovery features introduce choices about custody, identity, additional signers, or spending restrictions. These should be explicit product options with stated consequences for privacy and user control, not described as free improvements. Cashu extensions and wallet recovery designs need separate assessment from the baseline bearer workflow.

Dispute resolution also needs to distinguish a technical payment dispute from a commercial dispute. Successful transfer does not prove satisfactory delivery of goods. Merchants can retain receipts and contractual evidence without publishing every holder's transaction history. A private mint should explain what evidence it can furnish and what it intentionally cannot reconstruct.

## 9. Backing, solvency, and redemption

Neither a ledger entry nor a signed proof establishes an issuer's solvency. Native BTC and ETH are not ordinarily claims against an issuer promising conversion. ERC-20 tokens and Cashu units can represent issuer-backed claims, but need not all promise the same asset or conversion right.

For an issuer-defined unit, ask who owes what, to whom, when, and subject to which conditions. Distinguish reserve assets from assets actually available to holders, and nominal parity from a legally enforceable redemption promise. A compute-credit unit might entitle its holder to a service rather than cash. A warehouse unit needs delivery and custody terms. Accounting architecture cannot substitute for those definitions.

Clear's Cashu-derived model decouples issuance from a mandatory Bitcoin or Lightning funding loop. A Clear Mint Unit (CMU), identified by its exact `cmu-<keyset-id>`, obtains its institutional meaning from treasury authorization and unit policy. Different CMUs on one service must not be assumed interchangeable or mutually guaranteed. See [Cashu, Decoupled: Treasury Mint Model](CASHU-DECOUPLED-TREASURY-MINT-MODEL.md).

## 10. Auditability without unnecessary surveillance

Public visibility can make supply and transfer-state inspection easier, but does not by itself establish external reserves, beneficial ownership, or complete liabilities. A transparent contract can coexist with opaque custody.

For Clear, an audit program should examine authorized issuance, actual signing activity, retired obligations, reserve or service capacity, and redemption performance. Aggregate reporting can avoid collecting named holder balances. However, operator-provided totals alone are not independent proof that no unauthorized signatures were created. Controls around signing, independently examined records, and explicit assurance limitations remain necessary.

Useful disclosures include unit-specific outstanding obligations, authorization limits, backing definitions, redemption delays and failures, mint availability, reconciliation exceptions, and the scope and date of independent reviews. Reporting should distinguish gross swap activity from net issuance: replacement signatures are not automatically new economic liabilities. Small-cohort reporting also needs privacy review because aggregates can identify people when populations are tiny.

## 11. Community and public-system implications

Community currencies can make the issuer's obligation concrete: a cooperative service, local purchasing entitlement, or organizational resource allocation. Clear could support private circulation of such units without requiring each recipient to open an account with the treasury. The challenge is maintaining credible redemption, accessible wallets, and workable outage and recovery arrangements.

A larger public payment system adds scale, inclusion, essential-service continuity, governance legitimacy, and resolution concerns. The same privacy properties may be valuable, but a small community mint's trust arrangements cannot simply be assumed adequate nationally. Public deployment would need independent security evaluation, defined service standards, accessible alternatives during outages, and a legally grounded allocation of losses.

The policy choice is not simply blockchain versus no blockchain. It is which records should be shared, which powers should be distributed, which institutions should remain accountable, and what evidence holders need to rely on them.

## 12. Recommended Clear posture

1. Describe Mint Notes as holder-held evidence dependent on mint acceptance and unit-specific obligations, not trust-free digital objects.
2. Keep receipt, validation, successful swap, and external redemption distinct in documentation and wallet states.
3. Publish governance and redemption terms for each exact CMU, including existing-note treatment after policy changes.
4. Test concurrent spending, ambiguous responses, pending-state recovery, stale backups, and service failover before expanding reliance.
5. Offer meaningful aggregate assurance while limiting unnecessary holder identification and metadata retention.
6. Evaluate privacy, operator concentration, spending control, and redemption assurance separately rather than combining them into a single claim of decentralization.

**Bottom line:** Clear moves holding evidence toward the holder and issuance accountability toward a defined treasury, while retaining mint authority over proof acceptance. That is a distinct allocation of trust, not the disappearance of trust.

## Companion brief

[Where Is the Holding?](../website/policy-briefs/where-is-the-holding.md) presents the policy conclusions in shorter form.
