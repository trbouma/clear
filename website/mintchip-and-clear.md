---
title: MintChip and Clear
description: Comparing the Royal Canadian Mint's MintChip experiment with Clear's organization-issued Mint Notes.
---

# MintChip and Clear

MintChip was the Royal Canadian Mint's early-2010s attempt to explore digital
cash. Clear is a different project, but MintChip is a useful comparison because
it asked a nearby question: how can a digital instrument move with some of the
practical feel of cash, instead of behaving like a conventional card payment or
account transfer?

The similarity is strongest at the level of aspiration. Both systems care about
portable value, low-friction transfer, and cash-like use. The difference is in
what kind of value they represent, who issues it, how privacy is achieved, and
where trust lives.

## What MintChip was

MintChip was announced publicly in 2012 as a Royal Canadian Mint research and
development project. The Mint invited developers to build proof-of-concept
applications through the MintChip Challenge, which ran from April to August
2012 and offered prizes in gold. The project was explicitly experimental:
developers received access to MintChip technology to demonstrate possible uses
for digital payments.

MintChip was presented as an evolution of physical money for electronic use. In
contemporary descriptions, value was stored in secure integrated circuit chips
or secure asset stores. A payer and payee could exchange value directly,
including by NFC, SMS, email, or other channels, and transfers were intended to
work online or offline.

The Royal Canadian Mint later sold the MintChip assets to Loyalty Pays Holdings,
a subsidiary of nanoPay, in January 2016. The Mint described the divestiture as
a move from research and development toward private-sector commercialization.

## What Clear is

Clear is not a national digital-cash project. It is issuance, circulation and
redemption machinery for organization-defined transferable units.

A Clear issuer can define a food credit, service credit, member benefit,
allowance, voucher, refund credit, internal program unit, or other bounded
entitlement. A treasurer authorizes issuance or retirement. The mint signs
blinded Cashu outputs for one keyset-bound Clear Mint Unit, and holders carry
Mint Notes as bearer proofs.

Clear's unit is not "the Canadian dollar in digital form." Each Clear balance
belongs to a specific issuer, policy, mint, and `cmu-<keyset-id>`. Two Clear
programs can both display CMU, but they are not interchangeable unless an
explicit issuer policy makes them so.

## Comparison

| Question | MintChip | Clear |
| --- | --- | --- |
| Issuer model | A Royal Canadian Mint digital-cash technology later sold to nanoPay | Any organization or community operating a Clear mint under its own policy |
| Unit of value | Funds denominated in recognized national currencies | Issuer-defined transferable units denominated in a specific CMU |
| Main use case | Retail, ecommerce, person-to-person, B2B, and micropayment-style digital cash | Vouchers, credits, benefits, allowances, and other bounded organizational instruments |
| Custody model | Secure chips or secure asset stores hold balances and execute transfers | Wallets hold bearer Mint Notes; mint holds keyset secrets and spent-proof state |
| Transfer style | Direct value transfer between devices or asset stores, designed for online and offline use | Bearer proof transfer between wallets; mint needed for issuance, swaps, proof-state checks, redemption, and final retirement |
| Privacy model | Claimed cash-like privacy without personal identification for ordinary use | Blind signatures unlink issuance from later redemption better than account-ledger credits, while still admitting network and redemption metadata risks |
| Compliance posture | The 2016 Mint/nanoPay release emphasized regulatory compliance, including AML and KYC support | Compliance and eligibility are issuer-policy questions; Clear supplies verifiable issuance, proof validity, spent-state, and audit evidence |
| Trust anchor | MintChip secure hardware, platform rules, brokers, and later commercial operator | Issuer governance, treasurer signatures, mint operator custody, Cashu signatures, CMU identity, and ledger controls |
| Relationship to cash | Designed as digital cash for national-currency payments | Cash-like bearer notes for bounded organizational value; not legal tender and not universal money |

## The design resemblance

MintChip and Clear both recognize that ordinary electronic payments often lose
something useful about cash.

Cash can be handed over directly. The user does not need a credit account, a
card network authorization, or a merchant-specific account just to transfer a
small amount. MintChip tried to reproduce that feel by moving value between
secure devices. Clear tries to reproduce selected cash-like properties by
letting holders carry transferable Mint Notes locally and present them when a
recognized issuer or provider accepts that CMU.

Both designs therefore sit outside the classic "every holder has an account in
one application database" model. That matters for small payments, community
programs, limited-connectivity settings, and local trust networks.

## The key difference

MintChip tried to make national-currency value electronic and cash-like.

Clear tries to make organization-defined value portable and cash-like without
claiming that it is national money.

That difference changes almost everything. MintChip's hard problem was how a
government-linked digital cash platform could move dollar-denominated value
securely, privately, cheaply, and sometimes offline. Clear's hard problem is how
an organization can issue a bounded instrument that remains clear about who
stands behind it, what it represents, which CMU it belongs to, and what happens
when it is redeemed.

MintChip asked:

```text
How can Canadian-dollar value move like cash in digital channels?
```

Clear asks:

```text
How can an organization's promise or allocation move as a private bearer note?
```

## Hardware trust and cryptographic trust

MintChip leaned on secure hardware. The secure chip or asset store was the place
where balance changed. A transfer-out reduced the payer's stored value, and a
successful transfer-in increased the receiver's stored value. That is a natural
architecture for offline payments because the device itself must prevent copied
value from being spent twice while disconnected.

Clear leans on bearer proofs, blind signatures, and the mint's spent-proof
state. A wallet can hold and forward Mint Notes, but the mint is the final
double-spend authority when proofs are swapped, redeemed, or retired. This makes
Clear easier to run with ordinary software and compatible wallets, but it also
means Clear is not a complete offline-cash replacement. The note can travel
while the mint is unavailable; final confirmation still belongs to the mint.

The tradeoff is important:

- MintChip moves more double-spend prevention into trusted devices.
- Clear moves more double-spend prevention into the mint's ledger and Cashu
  proof validation.

Clear can eventually learn from offline-CBDC and secure-element work, but its
first obligation is to make online issuance, circulation, redemption, and
retirement reliable and understandable.

## Privacy comparison

MintChip was marketed as cash-like and usable without personal identification.
However, the Office of the Privacy Commissioner of Canada noted that available
implementation details raised questions. In the protocol it reviewed, messages
included payer and payee identifiers, and a payer certificate was included so a
signature could be verified. That did not necessarily mean every transaction
would be centrally stored, but it complicated any simple claim that MintChip
would be anonymous in the same way physical cash can be.

Clear's privacy story is different. With Cashu-style blind signatures, the mint
can issue a signed note without learning the final bearer secret it will later
see at redemption. That helps unlink issuance from redemption. It does not make
Clear perfectly anonymous. Wallet behavior, network addresses, timing, unusual
amounts, delivery relays, merchant workflows, and redemption context can still
leak information.

The better claim for Clear is modest: it can provide stronger transaction
privacy than ordinary named account balances for bounded issuer programs.

## Compliance and governance

MintChip's public materials eventually emphasized that the platform could
support regulatory compliance, including AML and KYC rules. That makes sense
for a national-currency payment platform. If a system moves dollar-denominated
value at retail scale, compliance cannot be an afterthought.

Clear should not copy that framing wholesale, because Clear is not one
universal payment network. It is a protocol and mint service for many separate
issuer-defined instruments. The compliance question depends on the instrument.
A meal voucher, a resort service credit, a refund credit, a securities-like
interest, and a general-purpose stored-value product may all face different
legal treatment.

Clear's responsibility is to keep the institutional facts legible:

- who issued the CMU;
- which treasurer authorized supply changes;
- what policy describes the instrument;
- which mint or cluster can redeem it;
- what evidence supports issuance and retirement; and
- why this CMU is not interchangeable with another one.

The issuer remains responsible for the legal meaning of the program.

## What Clear should learn from MintChip

MintChip is a useful predecessor because it took digital cash seriously before
today's CBDC debates became mainstream. It also shows how hard it is to replace
cash directly. Hardware distribution, merchant adoption, privacy expectations,
regulatory requirements, user experience, offline risk, and commercialization
all have to line up.

Clear can take a narrower path.

It does not need to digitize Canadian dollars. It does not need to become a
general-purpose retail network. It does not need every merchant to care. It can
serve organizations that already have a reason to issue bounded value and a
known set of people or providers who recognize it.

That narrower scope is not a weakness. It is what makes the system honest:

```text
MintChip: digital cash for recognized national-currency value
Clear: digital bearer notes for issuer-defined transferable units
```

## Where the projects meet

MintChip and Clear meet around a common intuition: digital payments should not
always require a central account relationship at the moment of transfer. People
should be able to hold value locally, move it directly, and present it with
limited disclosure.

They part ways on monetary ambition.

MintChip tried to bring cash into the digital economy as a broad payment
technology. Clear brings cash-like bearer mechanics to smaller domains of
recognition: communities, programs, clubs, facilities, and organizations with
specific promises to make and settle.

MintChip's history is therefore encouraging, but also clarifying. Clear should
borrow the cash-like goal, not the universal-cash burden.

## Sources

- Royal Canadian Mint, ["nanoPay Acquires MintChip(TM) from the Royal Canadian Mint"](https://www.newswire.ca/news-releases/nanopay-acquires-mintchiptm-from-the-royal-canadian-mint-565003491.html), January 12, 2016.
- Devpost, ["The MintChip Challenge"](https://mintchipchallenge.devpost.com/), 2012.
- Office of the Privacy Commissioner of Canada, ["Have Money, Will Travel: A Brief Survey of the Mobile Payments Landscape"](https://www.priv.gc.ca/en/opc-actions-and-decisions/research/explore-privacy-research/2013/mp_201306/), June 2013.
- Wired, ["Minting the Digital Currency of the Future"](https://www.wired.com/2012/05/mintchip/), May 2012.
