---
title: Old Function, New Tools
description: Clear applies modern cryptography to an organizational treasury function that is thousands of years old.
---

# Old Function, New Tools

Clear may look like a new kind of digital currency system. Its underlying
institutional model is much older.

Organizations have always needed to answer familiar questions: What resources
do we hold? Who may allocate them? Under what rules? Who carries out the
decision? What record proves that the decision was made properly?

Clear does not invent those questions or claim that software can settle them.
It gives an established treasury function a new way to issue, circulate, and
retire organization-defined value.

## Treasury before software

Some of the earliest surviving written records are administrative accounts.
At Uruk in southern Mesopotamia, large temple estates used clay tablets to
record economic activity and the distribution of revenues more than five
thousand years ago. The need for durable accounting was closely connected to
the development of writing itself. [The Metropolitan Museum of Art describes
these early records](https://www.metmuseum.org/essays/the-origins-of-writing)
as part of the administration of growing institutions.

Those systems also used physical seals to associate records and transactions
with responsible parties. The tools were clay, tokens, tablets, and cylinder
seals rather than databases and cryptographic keys, but the institutional
problem is recognizable: allocate resources, identify authority, and preserve
evidence. The Met characterizes these devices as early administrative
technologies accompanying the growth of cities and states in its discussion of
[a Sumerian ration record](https://www.metmuseum.org/art/collection/search/327069).

The comparison should not be stretched too far. Ancient accounting tablets
were not Cashu tokens, and an ancient seal was not a Nostr signature. The point
is simpler: shared resources have required authorization and accountable
recordkeeping for millennia.

## The corporate treasury pattern

Modern corporate treasury is one expression of the same durable need. It
manages an organization's financial resources, liquidity, obligations, and
risk in support of the organization's purposes. The
[Association for Financial Professionals](https://www.afponline.org/topics/treasury/treasury-management-defined)
describes treasury management in terms of overseeing financial resources and
ensuring that funds remain available for operational needs.

The mechanics vary by organization, but the recurring pattern is clear:

- a governing authority establishes policy and delegates responsibility;
- authorized officers make treasury decisions within that policy;
- operational staff and systems execute those decisions;
- books and controls preserve the resulting evidence; and
- audit or oversight makes the exercise of authority reviewable.

Clear adopts this pattern rather than replacing it.

## A Board of Internal Economy

The Canadian House of Commons offers a particularly useful institutional
analogy. Its Board of Internal Economy is the governing body responsible for
policies concerning the use of House funds, goods, services, and premises. It
delegates implementation and day-to-day management to the Clerk and House
Administration. That division is described in the House of Commons'
[official Board of Internal Economy overview](https://www.ourcommons.ca/boie/en/faq).

The analogy is not that Clear reproduces Parliament's legal structure. It is
that governance and operation are different functions:

| Familiar institution | Clear role |
| --- | --- |
| Governing body or constitutional authority | Currency root authority |
| By-laws, resolutions, and delegated mandates | Root-signed policy event |
| Authorized financial officers | Treasurers |
| Administration operating under policy | Mint operator |
| Accounting system and internal controls | Currency ledger and mint rules |

The Board establishes and enforces the governing rules while administration
implements them. In Clear, the currency root authority signs the policy while
the mint operator installs and runs it. The operator cannot rewrite the policy
merely because they control the server.

This distinction is a feature, not procedural overhead. It keeps technical
administration from quietly becoming institutional authority.

## Community treasury and vouchers

The same model applies beyond corporations and public institutions. Churches,
food banks, mutual-aid groups, service clubs, community foundations, and
emergency-response organizations all need ways to coordinate limited resources
under a shared mandate.

A Clear currency could operate as a community voucher system. Consider a group
of participating food banks and local service providers:

1. The governing organization establishes what the vouchers represent, who may
   receive them, where they are accepted, and how providers are reimbursed.
2. An authorized treasurer issues a specific amount of vouchers under that
   policy.
3. Individuals hold the vouchers as private Cashu proofs rather than as entries
   in a centrally visible recipient account.
4. Participating food banks or service providers accept the proofs because they
   recognize that particular issuer and Clear currency.
5. Providers return accumulated proofs for retirement and receive the
   reimbursement, replenishment, or accounting recognition promised by the
   organization's policy.

```text
Community authority establishes the program
                   |
                   v
Treasurer issues vouchers to participants
                   |
                   v
Recognized providers accept the vouchers
                   |
                   v
Providers return proofs for retirement and settlement
```

The limited recognition is intentional. These vouchers do not need to become
universal money. Their value comes from a clear promise made by a known
organization and recognized by a defined network of participants. A food-bank
voucher and a church transportation voucher remain separate currencies even if
both use Clear.

Clear handles issuance evidence, bearer proofs, swaps, spent-state checks, and
retirement. It does not decide eligibility or perform the real-world settlement
owed to a provider. The organization might reimburse a grocer, replenish a
food bank's inventory, recognize an internal budget transfer, or simply close
an allocation when proofs are retired. Those consequences belong in the
program's published policy and accounting process.

This approach can be especially useful when several independent providers need
to cooperate without placing every recipient and transaction inside one shared
application database. Providers choose which currencies they recognize, and
holders can present proofs without treating a friendly label such as "food
points" as sufficient evidence of who stands behind them.

## Cash-like, not legal tender

Clear is intended to recover useful qualities of cash inside these community
arrangements: a person can hold a bearer instrument locally, choose when and
where to present it, transfer it directly, and use it without maintaining a
conventional account at the mint. Participating providers can decide for
themselves whether to accept it.

Cashu's blind-signature design helps unlink the creation of a proof from its
later redemption. This can provide substantially more privacy than a shared
account ledger in which every transfer is attached to a named user. The
[Cashu documentation](https://docs.cashu.space/faq) also makes an important
qualification: protocol privacy is not complete anonymity. Wallet software,
network addresses, timing, unusual denominations, relay traffic, and the point
of redemption can still reveal information.

The design goal is therefore **cash-like privacy and optionality**, not a
guarantee that every use is unobservable.

Clear currencies are not intended to be legal tender. Legal tender is a legal
status attached to a jurisdiction's officially recognized money. In Canada,
for example, the
[Bank of Canada describes legal tender](https://www.bankofcanada.ca/2021/01/about-legal-tender/)
as money approved for paying debts. A Clear voucher makes no such claim. No one
outside its participating network is expected or required to recognize it, and
even participants accept it because of an agreement with the issuing
organization rather than because Clear declares it to be money.

That limited recognition is what makes Clear useful as a coordination
technology. A community does not need to reproduce the entire monetary system.
It needs a portable way to represent a particular allocation among people and
providers who understand its purpose.

The wider cash economy can remain underneath the arrangement:

```text
Donations, budgets, or ordinary money fund a community program
                            |
                            v
Treasurer issues purpose-specific Clear vouchers
                            |
                            v
Participants choose among recognized providers
                            |
                            v
Providers return vouchers and receive ordinary settlement
```

A church can fund a meal program in ordinary money while issuing private meal
vouchers to participants. A coalition of food banks can recognize one voucher
currency while retaining separate operations. A community foundation can
allocate transportation or emergency-service credits that circulate only
among participating providers. In each case, ordinary money can fund the
program and reimburse providers, while Clear supplies the portable instrument
that coordinates access between those two moments.

The result is not a rival to cash. It is a way to reproduce selected cash-like
properties inside a specific community of recognition: flexible possession,
direct presentation, user choice, limited disclosure, and voluntary
acceptance.

## What Clear changes

Clear changes the instruments available to the treasury, not the need for a
treasury.

- A signed Nostr policy event records delegated authority in a form the mint
  can verify independently.
- Treasurer signatures authorize specific issuance and retirement actions.
- Cashu blind signatures allow issued value to circulate as private bearer
  proofs rather than remaining an account entry in one application.
- A currency-specific ledger records supply changes and prevents double
  spending.
- Local-first operation lets an organization preserve its policy, ledger, and
  service continuity on infrastructure it controls.

These capabilities can make delegation more portable and evidence more
verifiable. They do not decide whether an issuance was wise, whether a policy
was fair, or whether an organization will honour its promises. Those remain
human and institutional responsibilities.

## The app is not the authority

This is the central design principle.

Clear verifies that an instruction was signed by a treasurer recognized under
the active policy. It verifies amounts, limits, approvals, proof signatures,
and spent state. It preserves evidence of what happened.

Clear does not appoint the treasurer. It does not create the organization's
mandate. It does not turn possession of a server password into legitimate
authority. The currency root authority and the organization behind it remain
responsible for those decisions.

Seen this way, Clear is deliberately modest. It is not a theory of governance
encoded into an app. It is infrastructure that allows an existing governance
arrangement to express authority precisely and carry out treasury decisions
with private, transferable digital instruments.

## Early tools for a very old practice

There is plenty left to learn. Different organizations will need different
thresholds, limits, disclosure practices, recovery procedures, and
relationships between governing bodies and treasurers. Clear is still an early
experiment, and its signed policy and multi-treasurer model remain under
development.

That is also why the old institutional pattern is useful. We do not need to
invent governance from first principles. We can begin with practices that
communities, corporations, associations, and public institutions already
understand, then test where cryptographic proofs and local-first infrastructure
make those practices more resilient, private, and portable.
