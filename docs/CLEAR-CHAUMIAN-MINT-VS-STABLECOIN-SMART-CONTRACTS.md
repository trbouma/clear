# Clear as a Chaumian Mint vs Stablecoin Smart Contracts

Status: Analysis note

## Purpose

Clear can be misunderstood if it is compared only to stablecoins, blockchains,
or tokenized payment rails. A stablecoin smart contract and a Clear mint may
both present transferable digital units, but their mechanisms are different at
nearly every layer.

This note compares Clear's Chaumian-mint model with common blockchain
stablecoin smart contract schemes. The focus is mechanism, not legal
classification. A particular stablecoin, voucher, security, benefit, or stored
value product may have its own legal obligations. The technical distinction is
that Clear issues private bearer Mint Notes under an issuer policy, while a
stablecoin contract usually maintains public account balances on a blockchain.

## Short version

Stablecoin smart contracts usually work like this:

```text
issuer or admin mints token balance
  -> contract records balances by blockchain address
  -> users transfer by submitting transactions
  -> validators order transactions into public blocks
  -> contract updates account balances
```

Clear works like this:

```text
treasurer authorizes issuance for one CMU
  -> mint signs blinded outputs for that CMU
  -> holder receives bearer Mint Notes
  -> holders transfer notes directly
  -> issuing mint later checks spent state at swap, redemption, or retirement
```

The stablecoin mechanism is account-state transfer on a public or permissioned
ledger. The Clear mechanism is Chaumian bearer-note issuance and redemption
against a mint's double-spend state.

## Mechanism comparison

| Dimension | Stablecoin smart contract scheme | Clear Chaumian mint |
| --- | --- | --- |
| Primary state | Public or permissioned contract state: balances, allowances, admin roles, events | Mint-side keysets, issued supply evidence, spent-proof state, treasury policy, CMU metadata |
| Holder asset | A balance assigned to a blockchain address | Bearer Mint Notes held locally by a wallet |
| Transfer act | Signed blockchain transaction calling `transfer`, `transferFrom`, or similar | Delivery of bearer proofs from one holder to another, followed by validation or refresh with the mint |
| Double-spend prevention | Blockchain consensus orders transactions and prevents the same balance from being spent twice | Issuing mint tracks spent proofs and rejects reused notes |
| Privacy baseline | Transfers and balances are generally visible to chain observers unless additional privacy systems are added | Blind signatures unlink issuance from later redemption better than account ledgers, though network and redemption metadata can still leak |
| Unit identity | Contract address plus chain plus token metadata | Exact `cmu-<keyset-id>` plus issuer or policy domain plus mint route |
| Issuance authority | Contract owner, minter role, bridge, custodian, or algorithmic controller | Treasurer or root-authorized policy action for a specific CMU |
| Redemption | Usually handled by issuer, custodian, bridge, or off-chain process outside the token transfer itself | Core part of the mint lifecycle: Mint Notes are redeemed or retired by the issuing mint under policy |
| Freeze or seizure | Often implemented through blacklist, pause, admin transfer, or upgrade controls | Not a normal property of already-held bearer notes; policy controls issuance, redemption, retirement, and acceptance |
| Composability | Strong on-chain composability with decentralized exchanges, lending protocols, bridges, and wallets | Strong wallet-level bearer transfer and issuer redemption; not inherently a smart-contract execution substrate |
| Failure mode | Chain congestion, contract bug, bridge failure, admin key compromise, custodian failure, chain reorg or fork | Mint outage, keyset compromise, spent-state failure, treasurer authority compromise, issuer non-performance |

## What users hold

In a stablecoin contract, a user normally holds a private key controlling a
blockchain address. The token balance is not a separate bearer object. It is an
entry in contract state:

```text
balances[0xUserAddress] = 100
```

The user can authorize the contract to update that state, but the spendable
asset is the account balance as recognized by the contract.

In Clear, a user holds Mint Notes. A Mint Note is a bearer proof denominated in
one Clear Mint Unit (CMU). The issuing mint can verify the proof and determine
whether it has already been spent. The holder does not need a named account
balance at the mint for every transfer.

```text
wallet
  -> Mint Note: 1 cmu-<keyset-id>
  -> Mint Note: 4 cmu-<keyset-id>
  -> Mint Note: 16 cmu-<keyset-id>
```

That difference matters. Stablecoin transfer normally mutates shared account
state immediately. Clear transfer can move bearer instruments between holders,
with final confirmation occurring when the receiver refreshes, swaps, redeems,
or retires the proofs with the mint.

## Where the ledger lives

Stablecoin smart contracts externalize the ledger to a blockchain. The token
contract depends on validators, sequencers, or block producers to order
transactions and publish the resulting state. Every observer who can read the
chain can usually reconstruct balances, transfers, and contract events.

Clear keeps its operational ledger at the mint. The mint must know enough to:

- advertise keysets and CMUs;
- issue signed Mint Notes after valid authorization;
- reject already-spent proofs;
- account for supply, redemption, and retirement;
- record treasury authorization evidence; and
- preserve recovery and audit checkpoints.

The mint does not need to publish every holder-to-holder transfer to a global
ledger. That is the source of the privacy difference and also the source of a
different trust boundary. Clear relies on the responsible mint or mint cluster
for spent-state finality; a stablecoin relies on blockchain consensus and the
token contract's state transition rules.

## Issuance authority

A stablecoin contract usually has one or more privileged mechanisms:

- a minter role can create tokens;
- a burner role can destroy tokens;
- an owner or governance system can change roles;
- an upgrade authority can replace implementation logic;
- a pause or blacklist role can restrict transfers; and
- an off-chain custodian may hold reserve assets.

These controls can be useful, but they make the stablecoin a contract-governed
account system. Users receive balances inside that contract's administrative
surface.

Clear separates authority from operation differently. A treasurer authorizes
supply-changing actions for a specific CMU under policy. The mint signs blinded
outputs and maintains spent state. A root or governance authority may appoint
treasurers, authorize keysets, or define policy. These roles should remain
separate even when one organization fills more than one role.

```text
currency root or issuer policy
  -> appoints treasurer and authorizes CMU policy
  -> treasurer signs issuance or retirement authorization
  -> mint signs blinded outputs and tracks spent state
```

The issuer's obligation sits outside the cryptographic proof. The proof shows
that the mint issued a valid note for a CMU and has not yet accepted it as
spent. The issuer policy explains what the note means.

## Privacy mechanism

Most stablecoin contracts use transparent account state. Even if the legal
owner of an address is not known at first, the activity graph is usually public:

```text
address A -> address B -> exchange C -> address D
```

Privacy can be added through mixers, shielded pools, confidential-transfer
systems, layer-2 designs, or permissioned ledgers, but those are additional
mechanisms beyond a typical stablecoin contract.

Clear uses Chaumian blind signatures. In broad terms:

```text
wallet blinds message
  -> mint signs blinded message
  -> wallet unblinds signature
  -> later holder presents signed proof
```

The mint can verify its signature when the proof returns, but the blind signing
flow helps prevent the mint from trivially linking issuance to later redemption.
This is not perfect anonymity. Wallet behavior, network routes, timing,
amounts, merchant context, redemption location, and unusual proof patterns can
still leak information. But the privacy primitive is native to the Clear
mechanism, whereas most stablecoin contracts begin from visible account state.

## Transfer and finality

Stablecoin finality is tied to the chain. A transfer is final enough when the
transaction has been included and the relevant settlement assumptions are
satisfied. The user waits for block inclusion, confirmations, or sequencer
finality.

Clear finality is tied to proof state at the mint. A receiver may receive a
Mint Note directly from another holder, but should treat it as pending until it
has verified, refreshed, swapped, redeemed, or retired the note with the
issuing mint. The mint's spent-proof decision is the double-spend barrier.

```text
received bearer note
  -> check correct CMU and mint
  -> contact issuing mint
  -> mint verifies signature and unspent state
  -> wallet marks note confirmed after successful refresh or redemption
```

This makes Clear closer to digital bearer cash than to a blockchain payment
rail. The recipient's wallet must be careful: possession of a token string is
not the same as final acceptance if the proof has not been checked against the
mint's spent state.

## Unit identity and interchangeability

A stablecoin unit is commonly identified by:

```text
chain + contract address + token metadata
```

A wrapped or bridged version of the same brand on another chain is a different
contract instrument, even if user interfaces display the same ticker.

Clear has a similar need for exact identity, but the identifier is bound to the
mint keyset:

```text
cmu-<keyset-id>
```

Two Clear balances are not interchangeable merely because both display `CMU`.
They are interchangeable only when they belong to the same recognized issuer
policy and complete CMU identity. Keyset rotation creates a new CMU unless the
issuer publishes an explicit migration or exchange policy.

This is one reason Clear is not trying to create a universal token ticker. It
is built for plural issuer-defined units whose boundaries remain visible.

## Redemption and reserve meaning

Stablecoins often center on reserve claims: a token may represent a claim on
bank deposits, treasury bills, another cryptoasset, collateral in a lending
system, or an algorithmic stabilization mechanism. The smart contract moves the
token, but redemption usually depends on an issuer, custodian, bridge, or
protocol outside the simple token transfer.

Clear centers the issuer policy directly. A CMU may represent a food credit,
service credit, refund credit, compute credit, public-purpose benefit, internal
allowance, or another bounded entitlement. Redemption may deliver goods,
services, recognition, retirement, reimbursement, or another policy-defined
outcome. It does not need to mean conversion to dollars or another asset.

This makes Clear closer to minting and redeeming issuer-defined instruments
than tokenizing an existing money balance for blockchain transfer.

## Smart contracts and programmability

Stablecoin contracts are powerful because they live in a programmable on-chain
environment. Other contracts can hold, swap, lend, borrow, bridge, escrow, or
compose with the token. This creates a large automation surface.

Clear is intentionally not that kind of general smart-contract environment.
It does not ask every transfer to execute on a global virtual machine. Its
mechanism is narrower:

- mint authorized notes;
- let holders carry and transfer them;
- prevent double spending;
- redeem or retire them under policy; and
- preserve evidence of treasury actions.

Application logic can still exist around Clear. A point-of-sale system, compute
meter, benefit program, membership system, or treasury workflow can decide when
to issue, accept, redeem, or retire notes. But that application logic is not
the same thing as a public smart contract holding everyone's balances.

## Administrative controls

Many stablecoin contracts include administrative controls because issuers need
compliance, incident response, and operational safety. Common mechanisms
include pausing transfers, blacklisting addresses, freezing funds, upgrading
contract logic, or replacing minters.

Clear should not copy those mechanisms blindly. A bearer-note model changes the
control surface. Once a holder has a valid Mint Note, the mint cannot treat it
exactly like a mutable account balance. Clear can still enforce policy at
issuance, swap, redemption, retirement, keyset lifecycle, treasurer authority,
and acceptance boundaries. It can suspend a CMU or move it to redemption-only
status. But it should be honest that bearer instruments are not account rows
that can be edited in place.

This is a design feature and a governance responsibility. Clear's safety
mechanisms should be phrased in minting terms, not imported from account-based
stablecoins without adjustment.

## Risk comparison

Stablecoin smart contract risks include:

- contract bugs or unsafe upgrades;
- admin key compromise;
- bridge compromise;
- chain congestion or censorship;
- validator, sequencer, or reorg risk;
- reserve mismanagement;
- oracle or collateral failure for some designs;
- address deanonymization and surveillance; and
- frozen or blacklisted account balances.

Clear risks include:

- mint operator outage;
- keyset secret compromise;
- spent-state corruption or split-brain mint clustering;
- treasurer key compromise;
- issuer non-performance at redemption;
- wallet mishandling of bearer proofs;
- network metadata leakage;
- loss of local Mint Notes by the holder; and
- unclear issuer policy or acceptance boundaries.

Neither model removes trust. They place trust in different mechanisms.
Stablecoins shift much of the transfer mechanism to blockchain consensus and
contract code. Clear shifts issuance and redemption to a mint with Chaumian
privacy, explicit CMU identity, and issuer policy.

## Integration possibilities

The models can coexist.

A stablecoin could fund a Clear treasury, and the issuer could mint CMUs
against that treasury policy. A Clear CMU could represent a bounded claim that
is later settled through a stablecoin rail. A wallet could hold both
stablecoin balances and Clear Mint Notes. A bridge-like service could exchange
stablecoin payments for Clear issuance or redeem Clear notes into stablecoin
settlement.

Those integrations should remain explicit:

```text
stablecoin payment funds treasury
  -> treasurer authorizes CMU issuance
  -> Clear mints private bearer notes
  -> issuer redeems notes under policy
  -> optional stablecoin settlement occurs at redemption
```

The stablecoin rail does not become the CMU, and the CMU does not become a
smart-contract balance. Keeping that boundary visible is what lets Clear serve
organizations that need issuer-defined, redeemable, private bearer units
without turning every unit into a blockchain token.

## Design implications for Clear

Clear documentation and product language should emphasize these distinctions:

1. Clear is a minting system before it is a payment rail.
2. A CMU is identified by `cmu-<keyset-id>`, not by a ticker or contract
   address.
3. Mint Notes are bearer proofs, not account balances.
4. The mint's spent-state database is the double-spend boundary.
5. Treasury authorization is separate from mint operation.
6. Redemption is issuer-policy specific and need not mean reserve-dollar
   conversion.
7. Privacy comes from blind signatures and local bearer holding, not from a
   public ledger.
8. Stablecoins may be useful settlement assets around Clear, but they are not
   the same mechanism as Clear.

