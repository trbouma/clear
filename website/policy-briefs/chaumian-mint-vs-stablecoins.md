---
title: Clear Is Not a Stablecoin
description: How Clear's Chaumian mint model differs from blockchain stablecoin smart contract schemes.
---

# Clear Is Not a Stablecoin

Clear may look adjacent to stablecoins because it issues transferable digital
units. That comparison is useful only up to a point. The mechanisms are
different.

A stablecoin smart contract usually records token balances by blockchain
address. Users transfer value by submitting transactions to a chain, validators
or sequencers order those transactions, and the contract updates account
balances.

Clear works differently. A treasurer authorizes issuance for one Clear Mint
Unit (CMU). The mint signs blinded outputs for that CMU. Holders receive
private bearer Mint Notes. Those notes can move between holders, and the mint
later prevents double spending by checking whether a presented proof has
already been spent.

The difference is not cosmetic. It changes privacy, custody, transfer, finality,
redemption, and trust.

## The core distinction

Stablecoin systems are usually account-state systems:

```text
issuer or admin mints token balance
  -> contract records balances by blockchain address
  -> users transfer by submitting transactions
  -> validators or sequencers order transactions
  -> contract updates public or permissioned account state
```

Clear is a Chaumian bearer-note system:

```text
treasurer authorizes issuance for one CMU
  -> mint signs blinded outputs for that CMU
  -> holder receives bearer Mint Notes
  -> holders transfer notes directly
  -> issuing mint checks spent state at swap, redemption, or retirement
```

In a stablecoin scheme, the spendable asset is normally a balance recognized by
a smart contract. In Clear, the spendable instrument is a bearer Mint Note held
locally by a wallet.

## What the holder holds

A stablecoin holder usually controls a private key for a blockchain address.
The stablecoin balance itself lives in contract state:

```text
balances[address] = amount
```

The holder can authorize the contract to update that state, but the contract
remains the place where balances are defined.

A Clear holder holds Mint Notes. A Mint Note is a private bearer proof
denominated in one exact `cmu-<keyset-id>`. The mint can verify that the proof
was signed by the correct keyset and determine whether it has already been
spent. The holder does not need a named account balance at the mint for every
transfer.

This makes Clear closer to electronic bearer cash or voucher circulation than
to a blockchain token balance.

## Privacy starts from a different place

Most stablecoin contracts begin from visible or shared account state. Even when
the legal owner of an address is not obvious, the transaction graph can often
be read:

```text
address A -> address B -> exchange C -> address D
```

Privacy can be added to blockchain systems, but it is usually an additional
mechanism layered around the token.

Clear starts from Chaumian blind signatures. A wallet blinds a message, the
mint signs the blinded message, and the wallet unblinds the signature. Later,
when a holder presents the signed proof, the mint can verify its own signature
without trivially linking that proof to the original issuance event.

That does not make Clear perfectly anonymous. Wallet behavior, network routes,
timing, amounts, merchant workflows, redemption locations, and unusual usage
patterns can still leak information. But Clear's privacy primitive is native to
the minting mechanism rather than an afterthought around public account state.

## Double-spend prevention

Stablecoins prevent double spending through blockchain ordering. A token
contract accepts one transaction history, and the chain's consensus or
sequencer model decides which state transition happened first.

Clear prevents double spending through the issuing mint's spent-proof state.
When a Mint Note is swapped, redeemed, or retired, the mint verifies the proof
and marks it spent. If the same proof is presented again, the mint rejects it.

This means Clear's finality is mint finality. A receiver may possess a note, but
should treat it as pending until the wallet verifies, refreshes, swaps, redeems,
or retires it with the issuing mint.

## Issuance authority

Stablecoin contracts often depend on administrative roles: owner, minter,
burner, pauser, blacklist manager, upgrade authority, bridge operator, or
reserve custodian. Those roles are powerful because they govern the account
system in which token balances live.

Clear separates authority differently. A root or issuer policy appoints
treasurers and authorizes keysets. A treasurer authorizes supply-changing
actions for a specific CMU. The mint signs blinded outputs and maintains spent
state.

```text
issuer policy
  -> appoints treasurer and authorizes CMU policy
  -> treasurer signs issuance or retirement authorization
  -> mint signs blinded outputs and tracks spent state
```

The issuer's obligation is not created by a token ticker. It is defined by the
policy that says what the CMU represents and how Mint Notes are redeemed or
retired.

## Redemption means policy, not only reserves

Stablecoins often center on reserve value: dollars, treasury bills,
cryptoassets, collateral, or another asset backing the token. The smart
contract moves balances, while redemption depends on an issuer, custodian,
bridge, or protocol process around the contract.

Clear begins with issuer policy. A CMU may represent a food credit, service
credit, refund credit, compute credit, benefit unit, internal allowance, or
another bounded entitlement. Redemption may deliver goods, services,
recognition, reimbursement, retirement, or another policy-defined outcome.

It does not have to mean conversion to dollars. Clear's important question is:
what has the issuer promised, who recognizes the CMU, and what happens when a
holder presents Mint Notes back to the issuer or mint?

## Administrative controls do not translate directly

Many stablecoin contracts include controls such as pause, blacklist, freeze,
upgrade, and admin transfer. Those controls fit an account-based smart contract
system where balances are rows in shared state.

Clear should be governed in minting terms instead. A bearer-note system can
control issuance, redemption, retirement, keyset lifecycle, treasurer authority,
and acceptance boundaries. A CMU can be suspended or moved to redemption-only
status. But a held Mint Note is not the same as an editable account row.

That is a design responsibility. Clear should not import stablecoin controls
without asking whether they make sense for private bearer instruments.

## Where stablecoins can still fit

Stablecoins and Clear can coexist. A stablecoin payment could fund a Clear
treasury. A Clear CMU could represent a bounded claim that is later settled
through a stablecoin rail. A wallet could hold both stablecoin balances and
Clear Mint Notes.

The boundary should stay explicit:

```text
stablecoin payment funds treasury
  -> treasurer authorizes CMU issuance
  -> Clear mints private bearer notes
  -> issuer redeems notes under policy
  -> optional stablecoin settlement occurs at redemption
```

The stablecoin rail does not become the CMU. The CMU does not become a smart
contract balance. Clear is useful precisely because it gives organizations a
way to mint issuer-defined, redeemable, private bearer units without turning
every unit into a blockchain token.

## Why it matters

Policy makers, issuers, and infrastructure partners should not evaluate Clear
as though it were a new stablecoin contract.

The relevant questions are different:

- Who is authorized to mint this CMU?
- What does the issuer promise when notes are redeemed?
- Which mint or mint cluster maintains the spent-proof state?
- How are keysets created, rotated, suspended, or retired?
- Who recognizes the CMU for trade or redemption?
- What privacy metadata remains outside the blind-signature mechanism?
- What happens if the issuer, mint operator, or treasurer fails?

Those are minting questions, not merely payment-rail questions. Clear belongs
in the older institutional category of minting and redemption, implemented with
Chaumian cryptography, rather than in the narrower category of blockchain
stablecoin smart contracts.

For a deeper technical comparison, see the repository note
[Clear as a Chaumian Mint vs Stablecoin Smart Contracts](https://github.com/trbouma/clear/blob/main/docs/CLEAR-CHAUMIAN-MINT-VS-STABLECOIN-SMART-CONTRACTS.md).

