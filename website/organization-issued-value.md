---
title: Organization-Issued Value
description: How Clear lets an organization define, issue, transfer, and retire its own bounded units.
---

# Organization-issued value

Clear demonstrates a simple but consequential idea: an organization can issue
its own private, transferable units without pretending those units are cash or
placing every holder inside one central account application.

The units may represent food credits, member benefits, service allowances,
event credits, local vouchers, or another promise defined by the issuer. Clear
provides the Mint Notes, transfer mechanics, double-spend protection, and supply
accounting. The organization remains responsible for explaining and honouring
what the units mean.

## From a program to a transferable unit

```text
organization defines a program
  -> Clear mint derives a keyset-bound CMU
  -> treasurer issues CMUs
  -> treasury holds issued Mint Notes
  -> recipient receives a private Clear transfer
  -> participating wallets and providers recognize that exact CMU
  -> returned units can be retired
```

Each active keyset creates a canonical identifier such as:

```text
cmu-000051c14ceac8ee
```

A friendly name such as **Harbour Lab Credits** and unit alias such as
**credits** make the balance understandable. The complete mint URL and CMU
remain visible because they identify the issuer and unit that a wallet must
actually validate.

## Cash payments and Clear transfers

Clear is designed to sit beside cash, not blur into it.

| Cash | Clear |
| --- | --- |
| One sat-denominated Cash Balance | Several issuer-specific Clear Balances |
| Used for payments | Used for transfers of defined credits or units |
| Settles through Bitcoin, Lightning, or ecash mints | Settles under an organization's program policy |
| Broadly transferable | Transferable, but recognized within a bounded network |

A Clear transfer can represent an allocation, gift, reimbursement, benefit, or
exchange. Calling it a transfer keeps the wallet from implying that every CMU
is money or a cash equivalent.

## What works now

The current lab system can:

- deploy a Clear mint behind a public URL;
- issue CMUs into a local treasury wallet;
- report issued, retired, and circulating supply;
- select an exact transfer amount and retain change;
- discover Clear support through a recipient's NIP-05 address;
- deliver an encrypted kind `7379` transfer through NIP-59;
- let Acorn store the transfer separately from cash; and
- let Safebox Web display or delete the pending transfer.

This is a meaningful interoperability milestone across three independently
deployable products.

## What comes next

The next wallet stage will accept pending transfers into spendable Clear proof
state and enable onward transfers from an ordinary wallet. The production
authority stage will replace the privileged lab operator token with signed,
currency-scoped treasurer authorization.

Until those stages and an independent security review are complete, Clear
should be used only with test units carrying no promise of financial value.

[Read the milestone](https://github.com/trbouma/clear/blob/main/docs/TRANSFERABLE-CMU-MILESTONE-2026-08-17.md){ .md-button .md-button--primary }
[See how Clear is governed](governance.md){ .md-button }
[Get started](getting-started.md){ .md-button }

