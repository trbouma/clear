---
title: Clear
description: Organization-defined Cashu points with explicit issuance and retirement.
---

<section class="clear-hero" markdown>

<img class="clear-hero-mark" src="assets/clear-logo.svg" alt="Clear">

# Clear

<p class="clear-tagline">Private, transferable points for organizations and communities.</p>

<p class="clear-intro">Clear gives a treasurer an explicit way to issue and retire organization-defined value while Cashu provides blinded proofs, private transfer, and double-spend protection.</p>

[Why Clear?](why-clear.md){ .md-button .md-button--primary }
[Get started](getting-started.md){ .md-button }
[View the source](https://github.com/trbouma/clear){ .md-button }

</section>

## Points that can circulate

Many organizations already keep internal balances: program credits, community
funds, service allowances, emergency allocations, event points, or other
limited-purpose value. Clear explores what happens when those balances become
portable Cashu proofs instead of rows tied to one application account.

Once issued, Clear proofs can be held and transferred like other Cashu ecash.
The difference is at the boundary: no Lightning invoice creates or redeems the
points. A designated treasurer authorizes issuance and accepts proofs for
retirement according to the organization's own published policy.

<div class="clear-grid" markdown>

<article class="clear-card" markdown>

### Authorize

A treasurer approves a precise issuance amount. Clear does not infer authority
from a payment invoice.

</article>

<article class="clear-card" markdown>

### Circulate

Wallets hold blinded proofs and transfer them directly. The mint supports swaps
and prevents proofs from being spent twice.

</article>

<article class="clear-card" markdown>

### Retire

Returned proofs are permanently marked spent and recorded as retired supply.
No Lightning payout is implied.

</article>

</div>

## The rule that keeps Clear clear

<div class="clear-rule" markdown>

**Every Clear currency stands alone.** Its identity, balance, policy, issuer,
and risk remain distinct. Proofs from different Clear currencies must never be
summed, spent together, or presented as interchangeable.

</div>

People can see a friendly name such as **Harbour Credits** and the display unit
**pts**, but the intended protocol unit is bound to the currency root, for
example `pts.00a1b2c3d4e5f6`. That durable identity survives operational keyset
rotation and prevents unrelated organizational promises from appearing to be
one balance.

## Authority stays understandable

Clear separates the organization that governs a currency, the operator that
runs the mint, and the treasurers who authorize routine issuance and
retirement. Even when one person fills several roles, each role uses a distinct
key and leaves different evidence.

[See how Clear is governed](governance.md){ .md-button }

## A focused sibling product

Clear joins the local-first product family as a narrow mint service:

- **Safebox** gives people approachable record and payment workflows.
- **Acorn** holds portable keys, records, and Cashu proofs.
- **Grove** preserves encrypted blobs.
- **Spurline** preserves and synchronizes Nostr events.
- **Clear** issues and retires organization-defined points.
- **Mainstay** is the future unified application.
- **Lockbox** is the hardware-first local appliance.

Clear remains independently deployable. Mainstay and Safebox can eventually
make its currencies understandable without hiding who issued them or what each
one promises.

!!! warning "Experimental software"
    Clear is an early protocol and product experiment. It has not been security
    reviewed. Do not use it for financial value or critical accounting.
