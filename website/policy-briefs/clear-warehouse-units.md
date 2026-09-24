---
title: Clear Warehouse Units
description: How Clear can turn standardized warehouse entitlements into precise, privately circulating bearer units.
---

# Clear Warehouse Units

Warehouses have long done more than store goods. By issuing receipts or
warrants, they allow a claim on stored property to move without requiring the
property itself to move each time it changes hands.

Clear could extend that pattern into a private electronic medium through a
**Clear Warehouse Unit (CWU)**.

> A Clear Warehouse Unit is a fungible bearer unit representing a
> policy-defined entitlement to a measured quantity of eligible inventory held
> within a recognized warehouse or custody system.

A CWU is not a new protocol unit. Each one is a Clear Mint Unit (CMU), with the
canonical identity `cmu-<keyset-id>`. “CWU” describes the instrument and its
warehouse-backed purpose.

## From warehouse inventory to bearer units

The basic model is straightforward:

```text
eligible goods enter a recognized warehouse pool
  -> warehouse or registry confirms minting capacity
  -> treasurer authorizes CWU issuance
  -> Clear issues private bearer Mint Notes
  -> holders transfer the notes
  -> notes are redeemed and retired
  -> goods, a conventional warrant, or another entitlement is delivered
```

Clear supplies private circulation and double-spend protection. The warehouse
and governing policy supply the connection to physical goods.

That division matters. A cryptographically scarce Mint Note does not prove that
grain remains in a silo or metal remains unencumbered. Inventory and Mint Note
supply must be independently controlled and reconciled.

## One pool, one CMU

The central design rule is interchangeability:

> Goods belong in the same CWU only when holders can treat every represented
> unit as interchangeable under the same policy.

Different commodities require different CMUs. So may different classes,
grades, crop years, origins, certifications, warehouse regions, or redemption
terms.

For example:

```text
CWU-WHEAT-CWRS-1-2026
Commodity: wheat
Class: Canada Western Red Spring
Grade: No. 1
Crop year: 2026
Measure: 1 kilogram
Canonical identity: cmu-<keyset-id>
```

A 2026 No. 2 wheat unit should not become interchangeable with a 2026 No. 1
unit merely because both display “wheat.” A 2027 crop should not silently
replace the 2026 pool. Each economically distinct promise receives its own CMU.

One Clear mint can support the entire catalogue while keeping every pool
separate in authority, supply, backing, redemption, and risk.

## Agricultural commodities fit naturally

The model applies to metals, but it may be especially useful for agricultural
commodities:

- wheat by class, grade, and crop year;
- coffee by variety, grade, origin, and harvest;
- cocoa by grade, origin, and crop season;
- rice by variety, grade, and production year; and
- other storable goods governed by recognized inspection and warehouse rules.

Agriculture also exposes why precise policy is necessary. Moisture, quality,
ageing, spoilage, storage location, certification, and minimum delivery lots
can change the economic meaning of the claim.

If stored goods are regraded, the issuer should not edit the old CMU's label.
It should stop new issuance, disclose the impairment, move qualifying goods to
the correct pool, and offer an explicit conversion or loss process.

## A unit is not automatically a warrant

A legal warehouse warrant may identify particular goods and carry title or
bailment rights under governing law. Ordinary Clear Mint Notes are fungible
amounts under an issuer policy.

Calling a CMU “one kilogram of copper” does not by itself transfer title to
copper. The governing arrangements must state whether the holder has:

- ownership of a share of pooled goods;
- a bailment interest;
- a contractual right to delivery;
- a right to receive a conventional warehouse warrant;
- a right to sale proceeds; or
- only a claim against the issuer.

Where one unique warrant must remain tied to one particular lot, a fungible
CMU may be the wrong primary instrument. Clear may instead represent the
fungible payment or credit side while an authoritative warrant registry
continues to control title.

## The inventory rule

A warehouse-backed scheme needs one non-negotiable economic constraint:

```text
outstanding redeemable CWU supply
  <= eligible, unencumbered inventory
```

The warehouse or authoritative registry determines eligible inventory. The
treasurer authorizes issuance within that limit. The mint enforces the exact
CMU, authorization, supply accounting, and spent-proof state.

Public reporting should distinguish:

- issued, retired, and outstanding CWU;
- eligible and reserved inventory;
- unused minting capacity;
- pending redemptions;
- impaired or regraded inventory; and
- the source and time of the latest reconciliation.

This makes the trust structure visible. Clear proves what happened to Mint
Notes. Warehouse and inspection evidence supports what happened to the goods.

## Private circulation, controlled endpoints

The CWU model can preserve privacy between two institutional boundaries:

```text
controlled inventory and issuance
  -> private bearer circulation
  -> controlled redemption and delivery
```

The mint need not maintain a named account for every intermediate holder.
Physical redemption may still require identity, shipping, customs, tax, or
sanctions information. Privacy comes from not placing every transfer inside a
shared account ledger, not from pretending that physical delivery has no
compliance requirements.

## What the policy must settle

Every CWU needs a published policy defining:

- commodity, class, grade, year, measure, and eligible location;
- warehouse, registry, inspection, and treasury authorities;
- the legal nature of the holder's entitlement;
- issuance limits and inventory reconciliation;
- storage, insurance, inspection, handling, and delivery charges;
- deterioration, regrading, expiry, and substitution rules;
- minimum redemption quantities and delivery procedures;
- treatment of warehouse, issuer, or custodian failure; and
- governing law and dispute process.

The complete `cmu-<keyset-id>` remains the authoritative identifier. A friendly
code helps people understand the unit but cannot replace the signed policy.

## The policy opportunity

Clear Warehouse Units could create privately circulating claims on real goods
without forcing every transfer onto a public blockchain or a warehouse's named
account ledger.

They do not eliminate institutional trust. They concentrate it where it can be
made accountable: the warehouse controls the goods, inspectors establish
quality, the inventory registry establishes capacity, the treasurer controls
issuance, and the mint protects the bearer instrument from double spending.

That model could support commodity cooperatives, agricultural finance,
regional warehouse networks, processors, exporters, strategic reserves, and
other communities that need standardized goods to circulate as precise
claims before physical delivery.

## The policy takeaway

Clear can support many classes, grades, years, and locations without pretending
they are one commodity balance.

The result is not a generic token labelled “wheat” or “copper.” It is a
catalogue of exact warehouse entitlements, each with its own CMU, inventory
pool, authority, supply limit, redemption promise, and lifecycle.

For the detailed design and risk analysis, see
[Clear Warehouse Units](https://github.com/trbouma/clear/blob/main/docs/CLEAR-WAREHOUSE-UNITS-ANALYSIS.md).

