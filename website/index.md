---
title: Clear
description: Issuance, circulation and redemption machinery for organization-defined transferable units.
---

<section class="clear-hero" markdown>

<img class="clear-hero-mark" src="assets/clear-logo.svg" alt="Clear">

# Clear

<p class="clear-tagline">Private, transferable Mint Notes for organizations and communities.</p>

<p class="clear-intro">Organizations have always needed ways to allocate and circulate value. Clear provides the issuance, circulation and redemption machinery for organization-defined transferable units, using the Cashu protocol for private bearer notes and double-spend protection. Clear marries this age-old treasury function and responsibility with new protocols to unlock new ways for organizations and communities to coordinate value.</p>

[Why Clear?](why-clear.md){ .md-button .md-button--primary }
[Organization-issued value](organization-issued-value.md){ .md-button .md-button--primary }
[Get started](getting-started.md){ .md-button }
[View the source](https://github.com/trbouma/clear){ .md-button }

</section>

## Clear works alongside cash

Clear is not a replacement for Bitcoin, Lightning, or the Cashu mints that use
them. In a compatible wallet, sat-denominated funds from those mints form a
single **Cash Balance**: broadly transferable, general-purpose value that can
move between people and settle through the Bitcoin and Lightning networks.

Clear adds **Clear Balances** alongside that cash balance. The plural matters:
each balance holds a distinct issuer-defined **transferable unit** with its own
mint, Clear Mint Unit, and policy. A Clear balance may represent food credits,
service units, member benefits, event allowances, or other products and in-kind
services. It can circulate privately between wallets, but it is useful where
the relevant issuer and participating providers recognize it; it is not
presumed to be cash or universally interchangeable with another Clear balance.

## Mint Notes that can circulate

Many organizations already keep internal balances: program credits, community
funds, service allowances, emergency allocations, event credits, or other
limited-purpose value. Clear explores what happens when those balances become
portable Mint Notes instead of rows tied to one application account.

Once issued, Clear Mint Notes can be held and transferred like other Cashu
ecash. Their technical representation remains a Cashu proof.
The difference is at the boundary: no Lightning invoice creates or redeems the
notes. A designated treasurer authorizes issuance and accepts Mint Notes for
redemption and retirement according to the organization's published policy.

The working lab milestone now carries that model across product boundaries:
Clear issues CMUs into a treasury wallet, sends an encrypted transfer to a
NIP-05 address, Acorn stores the incoming kind `7379` transfer separately from
cash, and Safebox Web lets the recipient accept it into the corresponding
spendable Clear Balance.

[See the organization-issued value milestone](organization-issued-value.md){ .md-button .md-button--primary }

<div class="clear-grid" markdown>

<article class="clear-card" markdown>

### Issue

A treasurer authorizes a precise amount, and Clear issues the Mint Notes. Clear
does not infer authority from a payment invoice.

</article>

<article class="clear-card" markdown>

### Circulate

Wallets hold Mint Notes and transfer them directly. The mint supports swaps and
prevents the underlying Cashu proofs from being spent twice.

</article>

<article class="clear-card" markdown>

### Redeem

The issuer accepts returned Mint Notes under its policy. Clear marks them spent
and records retired supply without implying a Lightning payout.

</article>

</div>

## The rule that keeps Clear clear

<div class="clear-rule" markdown>

**Every Clear Mint Unit stands alone.** Its logical mint, keyset, balance, policy,
issuer, and risk remain distinct. Mint Notes from different logical mints or
CMUs must never be summed, spent together, or presented as interchangeable. A
logical mint may expose an operator-approved mint cluster when its members
synchronously coordinate authoritative state.

</div>

People can see a friendly name such as **Harbour Credits** and the abbreviation
**CMU**, pronounced as the letters “C-M-U,” but the canonical protocol unit is bound to the
active keyset, for example `cmu-00a1b2c3d4e5f6`. Keyset rotation creates a new
CMU. Any migration must be explicit and must not make unrelated organizational
promises appear to be one balance.

[Understand Mint Notes and CMU](mint-notes.md){ .md-button .md-button--primary }

## Authority stays understandable

Clear separates the organization that governs a transferable-unit program, the
operator that runs the mint, and the treasurers who authorize routine issuance,
redemption, and retirement. Even when one person fills several roles, each role
uses a distinct key and leaves different evidence.

[See how Clear is governed](governance.md){ .md-button }

## A focused Mainstay family product

Clear joins the Mainstay product family as a narrow, independently useful mint
service:

- **Safebox Web** gives people approachable record and payment workflows.
- **Acorn** safeguards user-controlled keys, funds, and records.
- **Grove** preserves encrypted blobs.
- **Spurline** preserves and synchronizes Nostr events.
- **Clear** provides issuance, circulation and redemption machinery for Mint
  Notes denominated in keyset-bound CMUs.
- **Mainstay** is the future unified application.
- **Lockbox** is the hardware-first local appliance.

Clear remains independently deployable. Mainstay and Safebox Web can make its
transferable units understandable without hiding who issued them or what each
one promises.

**Good boundaries, not barriers.** Clear remains the authority for its own Mint
Notes and proof state; it does not become the wallet, relay, application, or
universal issuer. Cashu and Nostr interfaces let the family cooperate without
blurring those responsibilities or making separate units interchangeable.

!!! warning "Experimental software"
    Clear is an early protocol and product experiment. It has not been security
    reviewed. Do not use it for financial value or critical accounting.
