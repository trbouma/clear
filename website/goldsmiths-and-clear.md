---
title: Goldsmiths and Clear
description: Historical context from early English goldsmith banking for Clear's treasury model.
---

# Goldsmiths and Clear

George Selgin's "Those Dishonest Goldsmiths" is useful background for Clear
because it revisits one of the standard origin stories of modern banking. The
familiar story says that 17th-century London goldsmiths took coin for
safekeeping, issued warehouse-style receipts, then secretly lent the stored coin
while pretending it remained untouched in the vault.

Selgin argues that this story is mostly myth. The goldsmiths did help build the
payments practices that fed into modern banking, including transferable notes
and deposit balances backed by fractional reserves. But the strongest evidence
does not show that they began by embezzling coins they were legally obliged to
store. It shows something more interesting for Clear: the difference between
custody, debt, authority, and transferable claims was already the central
problem.

That is the historical echo Clear should pay attention to.

## The useful analogy

The treasurer in Clear is like the goldsmith in the institutional sense: a
recognized party stands between stored or recognized value and transferable
claims that other people can carry.

The analogy is not exact. A 17th-century goldsmith often combined several roles
inside one person or house:

- safekeeper of plate, jewels, sealed bags, or coin;
- debtor to customers who left loose coin;
- cashier and bookkeeper for merchants;
- lender and broker;
- issuer of notes or transferable balances; and
- participant in a wider clearing and credit network.

Clear deliberately separates functions that historical goldsmith-bankers often
combined:

| Goldsmith-banking function | Clear responsibility |
| --- | --- |
| Customer brings coin, bullion, or plate | Organization recognizes resources, obligations, or program value |
| Goldsmith decides what can be paid or advanced | Treasurer authorizes issuance, redemption, or retirement |
| Goldsmith's books record balances and obligations | Clear ledger records supply changes and proof state |
| Goldsmith note circulates among holders | Mint Note circulates as a bearer Cashu proof |
| Goldsmith must honor demand for payment | Issuer must honor the published redemption or retirement policy |
| Vault and books remain operationally trusted | Mint operator protects keysets, database, and service continuity |

The design lesson is not that Clear should imitate early banking in every
respect. It is that the durable social function is recognizable: a trusted
treasury function turns an organization's resources or promises into instruments
that can circulate under understood rules.

## The paper's corrective

Selgin's central distinction is between two kinds of "deposit."

A special deposit or bailment is property held for safekeeping. The custodian is
expected to return the very same thing. In monetary history this was most
plausible when coins were sealed in a bag or locked in a chest, making the
specific property identifiable.

A general money deposit is different. Loose coin handed to a banker was usually
treated as money owed back, not as the customer's specific coins held in trust.
The banker became a debtor. The customer held a claim to repayment, often along
with payment services, convenience, interest, or bookkeeping.

Selgin's point is that many textbook accounts collapse these two arrangements
into one misleading story. They imagine warehouse receipts where the legal and
commercial relationship was often closer to debt. Goldsmiths were accused by
contemporaries of other misconduct, including usury, coin culling, clipping, and
exporting heavy coin. But Selgin finds no strong contemporary evidence that they
were widely accused of the particular modern charge: secretly lending coin left
with them only for safekeeping.

For Clear, the corrective is powerful: the legitimacy of an instrument depends
on what the issuer promised, what the holder understood, who had custody, and
what evidence proves the transaction.

## Receipts, notes, and Mint Notes

The goldsmith story is often told as if a circulating note were just a receipt
for a named pile of metal. Selgin argues that early goldsmith notes were better
understood as promises to pay on demand. They could move from hand to hand
because they represented an obligation of the issuer, not because each holder
owned a particular coin in the vault.

Clear Mint Notes also are not warehouse receipts for a specific object.

A Mint Note is a bearer instrument denominated in a specific Clear Mint Unit,
identified by its complete `cmu-<keyset-id>`. It can circulate because the mint
can verify its signature, prevent double spending, and redeem or retire it under
the issuer's policy. The holder does not need an account entry at the mint for
each transfer. The instrument moves; the mint later clears the presented proof.

That makes the policy boundary essential. A Clear Mint Note should always tell a
careful holder:

- which issuer or community stands behind it;
- which exact CMU it belongs to;
- which mint or mint cluster can redeem or retire it;
- what the note represents in the real world; and
- what limits, expiry, conversion, or settlement rules apply.

Without those facts, a holder has cryptographic evidence but not enough
institutional meaning.

## The treasurer as goldsmith

The phrase "the treasurer is like the goldsmith" works best when it points to
the goldsmith as a treasury intermediary rather than as a cartoon villain.

The treasurer is the human or organizational officer who causes a recognized
resource, entitlement, or obligation to become circulating units. A food-bank
treasurer may issue meal credits. A club treasurer may issue service credits. A
conference treasurer may issue participant allowances. In each case, the
treasurer's authorization is the bridge between off-chain institutional reality
and on-chain or protocol-level bearer instruments.

```text
organization holds resources or makes a promise
  -> treasurer authorizes a specific issuance
  -> Clear signs blinded outputs for one CMU
  -> Mint Notes circulate between holders
  -> issuer accepts notes back under policy
  -> Clear retires or accounts for the returned proofs
```

The goldsmith's historical authority came from reputation, location, books,
vaults, relationships with merchants, and the law of money deposits. Clear
turns part of that trust surface into explicit cryptographic evidence:
treasurer signatures, bounded grants, keyset-bound CMUs, supply ledgers,
double-spend checks, and audit records.

The social question remains. A signature can prove that a treasurer authorized
issuance. It cannot prove that the community should trust the treasurer, that
the issuer's promise is fair, or that the promised goods or services will be
available. Clear sharpens evidence; it does not replace judgment.

## Why role separation matters

The goldsmith-banker combined authority, custody, recordkeeping, lending, and
redemption in ways that made later interpretation easy to confuse. When
something went wrong, observers could ask several different questions at once:

- Was property merely stored, or was it lent to the goldsmith?
- Did the customer hold title to specific coins, or a claim against the banker?
- Was the note a receipt, a promise to pay, or a transferable debt?
- Was the failure caused by private misconduct, sovereign intervention, bad
  coinage, or ordinary credit risk?

Clear's architecture tries to prevent that kind of ambiguity by assigning names
and keys to different responsibilities.

The root authority governs the currency and appoints treasurers. The treasurer
authorizes routine supply-changing actions. The mint operator runs the service
and protects key material. The operational signer creates Cashu signatures only
after policy checks pass. The holder owns bearer Mint Notes, not the mint's raw
keyset secret and not an undifferentiated claim on every other CMU.

```text
root authority -> appoints and limits treasurers
treasurer      -> authorizes issuance and retirement
mint operator  -> runs infrastructure and protects custody
mint service   -> verifies policy and signs blinded outputs
holder         -> controls transferable Mint Notes
```

A small organization may put several of these roles in one person's hands at
first. Clear still names the roles separately so the organization can later
split them without changing what the instruments mean.

## The lesson about custody

Selgin's paper turns on a custody distinction: sealed or earmarked property is
different from loose money surrendered into a general account. Clear has an
analogous distinction.

Possession of a Mint Note is not possession of the mint's signing key. A holder
can transfer or redeem their own notes, but cannot issue arbitrary new notes.
Possession of a treasurer key is not possession of the keyset secret. A
treasurer can authorize bounded actions, but does not automatically get the raw
cryptographic material that signs Mint Notes. Possession of server access is
not governance authority. A mint operator may keep the service running, but
should not be able to appoint treasurers or rewrite currency policy merely by
controlling infrastructure.

This is where Clear intentionally improves on the old combined-house model. The
goldsmith's vault, books, promise, and discretion were deeply entangled. Clear
keeps the entanglement visible and reducible:

- treasurer private keys stay outside the mint;
- keyset secrets stay in mint custody during normal operation;
- CMU identity is bound to public keysets, not display names;
- grants and nonces limit replay and accidental overreach;
- retirement and redemption leave auditable supply evidence; and
- migration of key material is exceptional, explicit, and separately
  authorized.

## What not to learn from the myth

The wrong lesson is that every circulating private instrument is secretly a
fraud unless it maps one-for-one to a stored physical object. Selgin's point is
more careful: fraud depends on the promise made and the legal or institutional
relationship created.

Clear should therefore avoid both forms of confusion.

It should not present Mint Notes as if they were claims to specific stored
assets when the issuer's actual promise is a service credit, benefit, voucher,
allowance, or other bounded entitlement. But it also should not hide the issuer's
promise behind technical language. Holders should not have to guess whether a
CMU is a meal voucher, a membership credit, a refund credit, an internal budget
unit, or something else.

Clear does not make all of those instruments money. It gives each one a
transferable bearer form and a clearing process. The issuer supplies meaning.

## Historical context for Clear

The goldsmith episode belongs beside Clear's broader historical frame:
organizations have long needed accountable ways to allocate resources, delegate
authority, issue claims, accept claims back, and keep records.

Clay tablets, seals, tallies, goldsmith notes, corporate treasury ledgers, and
modern databases all solve versions of the same problem. None of them removes
the need to know who is trusted, what they promised, and what evidence proves
that the promise was honored.

Clear's contribution is narrower and more modern:

- blind signatures let holders receive and later redeem Mint Notes with better
  privacy than ordinary account-ledger credits;
- Cashu proofs make the bearer instrument portable between compatible wallets;
- keyset-bound CMUs prevent unrelated issuer promises from blending into one
  balance;
- treasurer signatures make routine authority verifiable without exposing the
  treasurer's private key to the mint; and
- local-first mint operation lets organizations keep issuance, redemption, and
  evidence close to their own governance.

Seen through Selgin's goldsmith history, Clear is not inventing a strange new
institution. It is rebuilding a very old treasury function with explicit
boundaries that earlier systems often left to custom, reputation, and contested
memory.

## Source note

This page is based on George Selgin, "Those Dishonest Goldsmiths," revised
January 20, 2011. The paper argues that London goldsmith-bankers did participate
in fractional-reserve banking, but that the popular story of clandestine
embezzlement of coins left strictly for safekeeping is unsupported by the
available contemporary and legal evidence.
