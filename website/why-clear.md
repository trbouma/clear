---
title: Why Clear?
description: Why organizations may need private, transferable Mint Notes.
---

# Why Clear?

Organizations often need to allocate value before they need a payment rail.
A community may distribute food credits, a program may allocate service units,
an event may issue participant credits, or an emergency team may need a local
clearing mechanism.

Conventional account systems can do this, but they place every transfer inside
one application and its central account database. Clear explores a different
model: the organization issues private bearer Mint Notes that people can hold
and transfer, while the mint prevents double spending.

## Settlement follows policy

A Lightning-backed Cashu mint issues Mint Notes after receiving bitcoin and
redeems notes to pay a Lightning invoice. Clear intentionally removes that
coupling.

The organization defines:

- who may authorize issuance;
- why Mint Notes are issued;
- what goods, services, obligations, or recognition they represent;
- when redeemed Mint Notes may be retired; and
- whether any conversion or expiry policy exists.

The software enforces Mint Note validity, double-spend protection, and supply
accounting. It does not invent the policy or guarantee the issuer's promise.

Clear also separates the people who establish that policy from those who run
the mint and those who authorize routine transactions. See
[How Clear Is Governed](governance.md) for the intended responsibility and key
model.

## Useful without becoming universal

Clear is not trying to create one universal CMU. Its value comes from making
each issuer, keyset-bound Clear Mint Unit, and organizational policy explicit.

A community fund and an employee benefit program may both display `CMU`, but
their complete `cmu-<keyset-id>` identifiers and issuing mints differ. They are
different obligations under different rules. Keeping them separate makes the
system more honest and leaves future exchange policies as explicit agreements
rather than accidental arithmetic.

## Community voucher networks

Clear can support a closed-loop voucher system for churches, food banks,
mutual-aid groups, and networks of participating service providers. A treasurer
issues voucher Mint Notes under the organization's policy, people present them
to providers that recognize that specific CMU, and providers eventually redeem
the notes for retirement and the reimbursement or accounting treatment
promised by the program.

The vouchers are useful precisely because recognition is bounded. They do not
need to be accepted everywhere, and unrelated voucher programs do not become
one balance merely because both display `CMU`. Clear supplies the private
transfer and note-accounting mechanism; the participating organizations define
eligibility, acceptance, and settlement.

Clear aims to give these vouchers cash-like flexibility: people hold them
locally, present or transfer them directly, and do not need a named balance at
the mint. Blind signatures provide transaction privacy, although wallets,
networks, and redemption locations can still reveal metadata. This is a privacy
design, not a promise of perfect anonymity.

Clear vouchers are not intended to function as legal tender. They are
voluntarily recognized instruments within a limited network. Ordinary money may
fund the program and reimburse participating providers; Clear coordinates the
purpose-specific allocation between issuance and redemption.

Read [Old Function, New Tools](old-function-new-tools.md) for the broader
connection between community vouchers, corporate treasury, and longstanding
institutional governance.

## Membership, hospitality, and service credits

A membership-based club can use Clear to issue credits that members redeem for
services inside a defined community. A co-working club, for example, might
issue Mint Notes for booking a desk by the day, reserving a boardroom by the
hour, using printing services, renting a locker, or attending a paid event.

The club operates the mint and publishes what its CMU represents. Credits may
be allocated through a membership plan, purchased separately, awarded through
a promotion, or returned as a refund. A visible schedule can express prices
such as 10 CMU for a desk-hour or 50 CMU for a boardroom-hour. Redeemed Mint
Notes are retired by the issuing mint, providing bounded supply and redemption
accounting without requiring every member to have a named balance at the mint.

Clear does not become the club's membership, booking, or facilities-management
system. Those systems continue to determine membership eligibility,
availability, reservations, pricing, expiry, and delivery of the service.
Clear supplies the private bearer instrument, transfer mechanism, and
double-spend protection. This is **good boundaries, not barriers**: the credit
can integrate with existing club operations without turning the mint into the
club's system of record.

Each club and keyset has a distinct `cmu-<keyset-id>`. Credits from two clubs—or
from two keysets operated by the same club—remain separate unless an explicit
issuer policy provides a conversion or migration.

The same pattern fits a small resort or cruise ship. The operator can issue
guest credits, staff allowances, activity vouchers, meal credits, or service
reimbursements that are recognized only within that property or vessel.
Guests might redeem them for excursions, equipment rental, dining, laundry,
printing, meeting rooms, or other onboard services. The operator's reservation
and point-of-sale systems still determine prices and deliver services; Clear
provides the bounded bearer credit and its clearing state.

This is especially useful where connectivity to distant infrastructure is
intermittent or intentionally limited. A locally operated Clear mint can keep
its own issuance, swap, redemption, and double-spend checks close to the
community it serves. The CMU remains an operator-defined credit—not legal
tender and not automatically interchangeable with another resort's, vessel's,
or keyset's notes.

## Local-first continuity

A Clear mint can run on organization-controlled infrastructure and does not
need a Lightning node to issue or retire Mint Notes. Once notes have been
issued, people can transfer them directly. They still need the mint to swap or
redeem notes, detect double spending, or obtain final confirmation, but
temporary mint unavailability does not erase the notes already in their
possession.
