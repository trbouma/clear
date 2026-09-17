---
title: Coinage and Clear
description: How Clear continues older practices of minting, recognition, and bearer circulation with digital treasury units.
---

# Coinage and Clear

Clear can sound novel because its instruments are digital, private, and
cryptographic. But the function it performs is old. For centuries and
millennia, communities have used mints to turn recognized authority, metal,
weight, marks, and public trust into portable objects that people could carry
and trade.

Clear does something similar with different materials. Instead of stamping
metal, it uses cryptographic keysets. Instead of a coin face, it uses a
keyset-bound CMU. Instead of handing over a disc of metal, holders transfer
private bearer Mint Notes.

Coins were not valuable merely because a machine struck them. A coin mattered
because some authority, issuer, city, ruler, mint, or recognized community stood
behind its weight, purity, symbol, and acceptance. Just as importantly, a coin
continued to circulate only when people were willing to receive it.

Clear preserves that older pattern:

```text
authority recognizes value or obligation
  -> mint creates a portable bearer instrument
  -> holders accept and transfer it
  -> recognized parties redeem, retire, or reissue it
```

The tools have changed. The institutional shape has not.

## Minting before modern money

Coinage did not begin as one universal system. Ancient Greek coinage was
fragmented across city-states, rulers, leagues, colonies, and trade zones. A
coin normally carried marks that identified its issuing authority and suggested
the standard under which it had been made. The issuing authority could choose a
weight standard, a metal, a type, and a design. Those choices made the coin
recognizable.

Recognition did not always stop at political borders. Some coins travelled far
from the city or ruler that issued them because traders found them trustworthy
or convenient. Athenian owls, for example, circulated widely outside Athens. In
other cases, local coins remained local, foreign coins were weighed or tested,
and several monetary standards operated beside one another.

This is the important historical baseline: coinage was often plural. Mints and
authorities issued distinct instruments into overlapping networks of
recognition.

Clear follows that plural model more than the modern idea of one national
currency balance. Each Clear Mint Unit is a distinct issuer-defined treasury
unit, identified by its complete `cmu-<keyset-id>`. A wallet may display
several Clear balances, but they remain separate promises under separate
policies.

## Authority and acceptance

Coins sit between authority and acceptance.

An authority can mint a coin, define its standard, require it for taxes or
public payments, and punish counterfeiting. But a coin used in trade must still
meet the practical test of acceptance. People ask familiar questions: Is this
coin recognized? Is it full weight? Is it debased? Is the issuer trusted? Will
someone else accept it from me?

That final question matters. A coin can carry the image of a ruler or city and
still fail in commerce if holders distrust it. Conversely, a coin can travel
well beyond the direct power of its issuer if merchants find it reliable.

Clear makes the same distinction explicit.

The root authority and treasurers can authorize a CMU. The mint can issue valid
Mint Notes. But use still depends on recognition:

- holders must be willing to receive the Mint Notes;
- providers or counterparties must recognize the issuer and CMU;
- redemption parties must know what the issuer promises;
- wallets must keep distinct CMUs separate; and
- the issuer must honor the policy that gives the notes meaning.

Cryptography can prove that a Mint Note was issued by the right keyset and has
not already been spent. It cannot force social acceptance. That is not a
weakness. It is how bearer instruments have always worked.

## Central mints and plural mints

Modern people often imagine coinage as a purely central-state function. That is
part of the history, but not all of it.

Many states guarded the right to mint because coinage carried fiscal,
political, and symbolic power. Yet history also includes delegated mints,
provincial mints, city mints, emergency mints, colonial or league coinages, and
local tokens. During war or administrative disruption, minting could become more
improvised. Regional authorities, armies, besieged towns, or recognized local
institutions sometimes produced money-like instruments because trade and payment
needed to continue.

The point is not that every local issue was good, lawful, or stable. The point
is that minting has long involved a relationship among:

- the authority that permits or recognizes issue;
- the mint that makes the instrument;
- the standard that lets others evaluate it;
- the people who accept it; and
- the redemption, tax, trade, or settlement context that gives it practical use.

Clear separates those parts into named roles. The root authority governs the
unit. A treasurer authorizes routine supply changes. A mint operator runs the
infrastructure. The mint service signs blinded outputs and checks spent state.
Holders decide whether to accept and carry the resulting Mint Notes.

That separation makes Clear less mysterious. It is a digital minting stack for
recognized communities, corporations, delegated authorities, public-purpose
programs, and compute-credit systems, not a claim that software has become the
sovereign.

## Payment rails are not coinage systems

Most digital-money systems are payment rails. A blockchain moves tokens. A
stablecoin moves a claim defined somewhere else. A card network routes an
authorization. A Lightning invoice settles a sat-denominated payment. These
systems can be powerful, but they usually assume the unit already exists.

Coinage asks a different question: how does a unit come into existence as a
recognized bearer instrument?

Clear is built around that question. It defines a minting path:

```text
policy defines the unit
  -> authority appoints or recognizes treasurers
  -> treasurer authorizes issuance
  -> mint creates bearer notes for one CMU
  -> holders circulate them
  -> issuer redeems or retires them
```

That is why Clear can support more than community vouchers. The same structure
can express a corporate credit, a public-purpose treasury unit, a delegated
mint's local instrument, or a compute-credit allowance for agents. Those are
not the same legal or economic thing, but they share a minting lifecycle.

## Marks, metal, and keysets

Physical coins used visible and material evidence.

A coin's stamp identified the issuing authority. Its metal, weight, and sound
could be inspected. Its design made it recognizable. Its wear, clipping, or
debasement could raise suspicion. A merchant did not need to know every private
decision inside the mint to evaluate the coin, but they did need enough public
evidence to decide whether to accept it.

Clear replaces those physical signals with cryptographic and policy evidence.

| Coinage signal | Clear signal |
| --- | --- |
| Mint mark, ruler, city, or symbol | Issuer, policy, and logical mint identity |
| Weight and metal standard | CMU identifier and denomination set |
| Die-struck design | Public keyset descriptor |
| Assay, weighing, or testing | Signature verification and proof-state check |
| Counterfeit detection | Cashu proof validation and spent-proof state |
| Recall, recoinage, or reminting | Redemption, retirement, migration, or explicit exchange policy |

A coin is not just metal. A Mint Note is not just bytes. In both cases the
instrument combines technical form, issuer meaning, and social recognition.

## What Clear replicates

Clear replicates the old minting pattern at the level of function:

1. An authority or community defines what kind of value is being represented.
2. A mint creates standardized bearer instruments under that authority.
3. The instruments move between holders without requiring every transfer to be
   an account entry at the issuer.
4. Recognition determines where the instruments are useful.
5. Redemption or retirement closes the loop and updates the issuer's books.

That loop is familiar in coinage, token, voucher, credit, and allowance
systems.

Clear's novelty is not that it discovered circulation. Its novelty is that it
uses Cashu blind signatures, keyset-bound CMUs, treasurer authorization, and a
spent-proof ledger to perform an old mint function with digital bearer notes.
It is coinage in electronic medium, not merely another network for routing
payments.

## What Clear does not replicate

Clear does not reproduce every property of coinage.

Physical coins can be inspected without a network. Clear Mint Notes can move
between wallets while the mint is unavailable, but final double-spend protection
comes from the mint's proof-state checks. A physical coin can sometimes
continue circulating after its issuer has disappeared, based on metal value or
custom. A Clear Mint Note depends more directly on a functioning issuer policy,
keyset, mint, and redemption context.

Clear also does not claim legal-tender power. A government can give official
money special status for taxes and debts. Clear does not do that. A CMU is
useful where an issuer, providers, and holders recognize it. That bounded
recognition is the point.

## People complete the mint

The most important part of coinage history for Clear is not the minting machine.
It is the accepting public.

Coins worked when people trusted the mark, the material, the issuer, and the
market around them. The authority created the coin, but holders made it
circulate. Trade tested the instrument continuously.

Clear should keep the same humility. A treasurer can authorize Mint Notes, and
Clear can prove their cryptographic validity. But a CMU becomes useful only
when people understand and accept the promise:

```text
This issuer stands behind this CMU,
under this policy,
for this use,
within this community of recognition.
```

That is why Clear keeps balances plural. A food credit, a service credit, a
refund credit, a state-recognized voucher, a compute credit, and a membership
credit should not collapse into one generic number. Their usefulness comes from
who recognizes them and what they can be redeemed for.

## A very old idea with new tools

Clear is not trying to replace the long history of minting with an app. It is
trying to make an old pattern usable in digital communities:

- mint recognizable bearer instruments;
- bind each instrument to an issuer and standard;
- let holders transfer them privately;
- prevent counterfeiting and double spending;
- preserve supply and retirement evidence; and
- leave acceptance to the people and institutions that understand the promise.

That is why coinage is such a good historical frame for Clear. The mint has
always been a bridge between authority and circulation. Clear rebuilds that
bridge with cryptographic keys instead of dies, Mint Notes instead of stamped
metal, and explicit CMUs instead of ambiguous local labels.

The old lesson still governs the new system: issue is not enough. The people
who hold, trade, and redeem the instrument complete the currency.

## Sources

- World History Encyclopedia, ["Ancient Greek Coinage"](https://www.worldhistory.org/Greek_Coinage/).
- Cambridge University Press, ["Choosing and Changing Monetary Standards in the Greek World during the Archaic and the Classical Periods"](https://www.cambridge.org/core/books/ancient-greek-economy/choosing-and-changing-monetary-standards-in-the-greek-world-during-the-archaic-and-the-classical-periods/E0C41775CFCA968E9866673608289607).
- Lawrence University, ["The Production of Ancient Coins: The Issuing Authority"](https://www2.lawrence.edu/dept/art/BUERGER/ESSAYS/PRODUCTION2.HTML).
- The Royal Mint, ["Explore Coinage During Conflict"](https://www.royalmint.com/stories/collect/explore-coinage-during-conflict/).
- Zane Mullins, ["The circulation and distribution of classical Greek coinage"](https://onlinelibrary.wiley.com/doi/full/10.1111/ehr.70069), *The Economic History Review*, 2025.
