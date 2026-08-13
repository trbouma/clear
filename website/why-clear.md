---
title: Why Clear?
description: Why organizations may need private, transferable internal points.
---

# Why Clear?

Organizations often need to allocate value before they need a payment rail.
A community may distribute food credits, a program may allocate service units,
an event may issue participant points, or an emergency team may need a local
clearing mechanism.

Conventional account systems can do this, but they place every transfer inside
one application and its central account database. Clear explores a different
model: the organization issues private bearer proofs that people can hold and
transfer, while the mint prevents double spending.

## Settlement follows policy

A Lightning-backed Cashu mint issues proofs after receiving bitcoin and melts
proofs to pay a Lightning invoice. Clear intentionally removes that coupling.

The organization defines:

- who may authorize issuance;
- why points are issued;
- what goods, services, obligations, or recognition they represent;
- when returned points may be retired; and
- whether any conversion or expiry policy exists.

The software enforces proof validity and supply accounting. It does not invent
the policy or guarantee the issuer's promise.

Clear also separates the people who establish that policy from those who run
the mint and those who authorize routine transactions. See
[How Clear Is Governed](governance.md) for the intended responsibility and key
model.

## Useful without becoming universal

Clear is not trying to create one universal points currency. Its value comes
from making each organizational currency explicit and portable.

A community fund and an employee benefit program may both display points, but
they are different obligations issued under different rules. Keeping them
separate makes the system more honest and leaves future exchange policies as
explicit agreements rather than accidental arithmetic.

## Community voucher networks

Clear can support a closed-loop voucher system for churches, food banks,
mutual-aid groups, and networks of participating service providers. A treasurer
issues vouchers under the organization's policy, people present them to
providers that recognize that specific currency, and providers eventually
return the proofs for retirement and the reimbursement or accounting treatment
promised by the program.

The vouchers are useful precisely because recognition is bounded. They do not
need to be accepted everywhere, and unrelated voucher programs do not become
one balance merely because both display points. Clear supplies the private
transfer and proof-accounting mechanism; the participating organizations define
eligibility, acceptance, and settlement.

Clear aims to give these vouchers cash-like flexibility: people hold them
locally, present or transfer them directly, and do not need a named balance at
the mint. Blind signatures provide transaction privacy, although wallets,
networks, and redemption points can still reveal metadata. This is a privacy
design, not a promise of perfect anonymity.

Clear vouchers are not intended to function as legal tender. They are
voluntarily recognized instruments within a limited network. Ordinary money may
fund the program and reimburse participating providers; Clear coordinates the
purpose-specific allocation between issuance and redemption.

Read [Old Function, New Tools](old-function-new-tools.md) for the broader
connection between community vouchers, corporate treasury, and longstanding
institutional governance.

## Local-first continuity

A Clear mint can run on organization-controlled infrastructure and does not
need a Lightning node to issue or retire points. Once proofs have been issued,
people can transfer them directly. They still need the mint to swap proofs,
detect double spending, or obtain final confirmation, but temporary mint
unavailability does not erase the proofs already in their possession.
