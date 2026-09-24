# Clear Warehouse Units

Status: Analysis note

## Purpose

This note develops the concept of a **Clear Warehouse Unit (CWU)**: a
fungible, privately transferable bearer unit representing a policy-defined
entitlement to measured inventory held within a recognized warehouse or
custody system.

The concept follows from the analysis of the London Metal Exchange (LME)
rulebook and its LMEsword warehouse-warrant system. That analysis showed both
an opportunity and a boundary. Clear can provide a bearer instrument associated
with warehouse-controlled goods, but cryptographic minting alone does not turn
a Clear Mint Unit (CMU) into a legal warehouse warrant, prove that inventory
exists, or establish title to a particular lot.

A CWU should therefore be understood as an instrument class built with Clear,
not as a new protocol identity. Every CWU remains an exact, keyset-bound CMU:

```text
Instrument class: Clear Warehouse Unit
Canonical identity: cmu-<keyset-id>
Human description: policy-defined commodity, grade, year, measure, and place
```

## Executive finding

Clear is well suited to represent **fungible claims on standardized inventory
pools**. It is less suited to represent a unique, indivisible warehouse warrant
whose legal effect depends on lot-specific attributes and a named account or
title registry.

The practical dividing line is interchangeability:

> Inventory belongs in the same CWU only when every represented unit can be
> treated as interchangeable under one custody, transfer, and redemption
> policy.

Where inventory differs materially by commodity, class, grade, crop or
production year, certification, location, delivery terms, or legal rights, it
should use a different CMU. The same Clear mint can operate many such CMUs
without merging their supply, backing, authority, or holder risk.

This creates a catalogue of precise warehouse instruments rather than one
generic “commodity token.”

## Warrant, receipt, entitlement, and unit

These terms should not be used interchangeably.

### Warehouse warrant

A warehouse warrant may be a document of title, evidence of bailment rights,
or another legally recognized claim to identified goods. Its effect depends on
the governing law, warehouse agreement, scheme rules, and the particulars of
the goods.

### Warehouse receipt

A warehouse receipt records that a warehouse received particular goods. Its
negotiability and legal effect vary by jurisdiction and scheme. A receipt can
be important source evidence without being the instrument that circulates in
Clear.

### Warehouse entitlement

A warehouse entitlement is the economic or legal right promised to the CWU
holder. Depending on policy, it might be:

- title to a fungible share of pooled goods;
- a bailment or co-bailment interest;
- a contractual right to delivery;
- a right to receive a conventional warehouse warrant;
- a right to sale proceeds; or
- a limited claim against the issuer rather than a proprietary interest in
  the goods.

The policy must select and define the entitlement. Clear cannot infer it from
the unit name.

### Clear Warehouse Unit

A CWU is the privately transferable bearer representation of a measured amount
under that policy. It is issued as Mint Notes denominated in a specific CMU.
The Mint Notes can circulate without placing every holder or transfer on the
warehouse registry.

```text
warehouse-controlled inventory
  -> authoritative inventory record
  -> treasury authorization within an issuance limit
  -> CWU Mint Notes
  -> private bearer circulation
  -> redemption and retirement
  -> delivery, warrant transfer, sale proceeds, or another policy consequence
```

## Why the CMU boundary matters

The canonical identity of every CWU is the complete `cmu-<keyset-id>`. A ticker
or friendly name is not enough.

Consider Canadian wheat:

```text
Display name: 2026 No. 1 CWRS Wheat Warehouse Unit
Short label: CWU-WHEAT-CWRS-1-2026
Measure: 1 kilogram
Canonical identity: cmu-<keyset-id>
```

Here, **CWRS** means Canada Western Red Spring. The abbreviation must be
expanded in holder-facing policy before it is used alone.

Another CMU might represent 2026 No. 2 Canada Western Red Spring wheat. A third
might represent No. 1 Canada Western Amber Durum wheat. Even when all three are
called “wheat,” they are not the same instrument.

The keyset boundary prevents a wallet or market from silently treating them as
one balance. Conversion between them must be an explicit exchange under a
published ratio or market price.

## Defining an inventory pool

A CWU policy should specify every attribute that determines whether inventory
is economically interchangeable.

| Dimension | Policy question |
| --- | --- |
| Commodity | What physical good is represented? |
| Class or variety | Which commercial or biological category qualifies? |
| Grade | Which quality standard and tolerances apply? |
| Production period | Does crop year, vintage, batch, or production year matter? |
| Unit of measure | Does one CWU represent a kilogram, tonne, bushel, litre, or other measure? |
| Certification | Must inventory be organic, fair trade, origin-certified, assay-certified, or otherwise verified? |
| Location | Which warehouse, port, region, or approved warehouse network can hold eligible goods? |
| Deliverability | What packaging, lot size, notice, and delivery point apply? |
| Custody status | Must goods be insured, unencumbered, segregated, or part of an approved commingled pool? |
| Time | What expiry, ageing, deterioration, or storage period applies? |
| Charges | Who pays storage, insurance, inspection, handling, tax, and delivery costs? |
| Legal claim | Does the holder receive title, bailment rights, a contractual delivery claim, or proceeds? |

If changing an attribute would cause a reasonable holder to reject substitution,
the inventory probably belongs in a different CMU.

## Metals and agricultural commodities

### Metals

Metals are comparatively durable, but they are not automatically fungible.
Grade, brand, assay, shape, weight tolerance, warehouse location, encumbrance,
and delivery terms can matter.

Examples include:

```text
CWU-CU-GRADE-A-ROTTERDAM
CWU-AL-P1020A-DETROIT
CWU-AU-995-LONDON
```

These labels are illustrative only. The complete CMU and policy remain
authoritative.

### Agricultural commodities

Agricultural goods introduce additional dimensions:

- crop year and harvest period;
- variety or class;
- grade, moisture, protein, foreign material, and other quality tolerances;
- origin and phytosanitary status;
- organic or sustainability certification;
- storage life, deterioration, infestation, and shrinkage;
- periodic inspection and regrading;
- fumigation, handling, and insurance obligations; and
- minimum economically deliverable lot size.

Examples could include:

```text
CWU-WHEAT-CWRS-1-2026
CWU-WHEAT-CWRS-2-2026
CWU-WHEAT-CWAD-1-2026
CWU-COFFEE-ARABICA-GRADE-1-2026
CWU-COCOA-GRADE-1-GHANA-2026
```

The ability to create precise CMUs is valuable here. A newer crop year does not
silently replace an older one, and a quality downgrade does not remain hidden
inside an unchanged token symbol.

## The supply invariant

The core economic control is simple to state:

```text
outstanding redeemable CWU supply
  <= eligible, unencumbered inventory available under the policy
```

Implementing that invariant is not simple. The mint knows how many Mint Notes
have been issued and retired. It does not independently know whether grain is
still in the silo, metal remains unencumbered, insurance is current, or a lot
has failed inspection.

The warehouse or authoritative inventory registry must therefore provide an
**issuance capacity** for each CMU. A treasurer may authorize issuance only
within that capacity.

```text
warehouse confirms eligible inventory
  -> inventory authority establishes minting capacity
  -> treasurer authorizes issuance
  -> mint verifies authorization and remaining capacity
  -> mint signs blinded outputs
  -> issued amount reduces available capacity
```

Redemption should reverse the relationship only when its real-world
consequence is recorded:

```text
holder presents CWU Mint Notes
  -> mint validates and marks proofs spent
  -> redemption authority allocates inventory or another entitlement
  -> Mint Notes are retired
  -> inventory and supply records are reconciled
```

Whether capacity becomes reusable after redemption depends on the policy. If
the goods leave the warehouse, capacity should normally fall with inventory.
If notes are redeemed only to move them between controlled accounts while the
goods remain eligible, the policy may permit reissuance. Issue, redeem, retire,
and release inventory must remain distinct events.

## Roles and separation of authority

| Role | Responsibility |
| --- | --- |
| Commodity scheme authority | Defines the instrument, eligible inventory, holder rights, and rule-change process |
| Warehouse or custodian | Possesses or controls the physical goods and maintains them under agreed conditions |
| Inspector, grader, or assayer | Determines whether goods satisfy the policy's quality requirements |
| Inventory registry | Maintains the authoritative record of eligible, pledged, released, and impaired inventory |
| Treasurer | Authorizes CWU issuance, redemption, and retirement within approved capacity |
| Clear mint operator | Protects keysets, signs blinded outputs, and maintains spent-proof state |
| Redemption agent | Coordinates delivery, warrant transfer, sale, or other promised performance |
| Auditor or overseer | Reconciles physical inventory, registry records, CMU supply, authority, and exceptions |
| Holder | Bears the instrument and decides whether the policy and issuer are acceptable |

One organization may fill several roles, but the evidence should keep them
distinguishable. A mint operator should not be able to increase eligible
inventory merely because it can operate the signing service. A warehouse
should not be able to create circulating supply without treasury authorization.

## Lifecycle by commodity, grade, and year

A seasonal CWU should have an explicit lifecycle:

```text
proposed
  -> approved for inventory admission
  -> active issuance and redemption
  -> issuance closed
  -> redemption only
  -> expired, converted, or fully retired
```

Closing issuance preserves the original instrument. It does not require
invalidating outstanding Mint Notes. Holders can continue to redeem according
to policy while no new supply is created.

### Regrading

If stored goods no longer meet the original grade, the system should not edit
the CMU description after issuance. It should instead:

1. suspend additional issuance against the affected inventory;
2. calculate the remaining eligible capacity;
3. disclose any shortfall or impairment under the governing rules;
4. move qualifying inventory to the correct pool; and
5. offer an explicit conversion, substitution, sale, or loss-allocation process.

Changing the label would erase the promise holders originally accepted.

### Crop-year conversion

An older crop-year CMU can be exchanged for a newer one only through an
explicit transaction. The ratio may account for quality, storage charges,
market price, or policy incentives.

```text
10 CWU-WHEAT-CWRS-1-2026
  -> retire old-year Mint Notes
  -> apply published conversion terms
  -> issue 9.8 CWU-WHEAT-CWRS-1-2027
```

The example ratio is illustrative. Conversion is not a key rotation. The old
and new CMUs represent different inventory pools and should retain different
canonical identities.

## Redemption design

The policy should define at least three redemption paths.

### Physical delivery

The holder retires enough CWUs to meet a minimum delivery lot and pays or
settles applicable charges. The warehouse releases goods under an external
delivery process. The mint receipt is evidence for that process, not physical
delivery itself.

### Conventional warrant or receipt

The holder retires CWUs and receives a conventional warehouse document or an
account entry in an authoritative registry. This allows private circulation to
end at a legally recognized custody boundary.

### Cash or proceeds

The issuer or agent sells inventory or applies a valuation rule and pays the
holder. If this is the ordinary promise, the CWU may economically resemble a
commodity-backed financial claim rather than a right to take delivery. The
policy and regulatory analysis should say so plainly.

Redemption must specify timing, fees, minimums, delivery location, identity
requirements, taxes, substitution rights, and the treatment of failed or late
performance.

## Privacy and inspection

Chaumian Mint Notes can separate issuance from later presentation, allowing
private bearer circulation. That does not make the warehouse or redemption
process anonymous.

Physical delivery commonly requires identity, shipping, customs, tax, or
sanctions information. A scheme may therefore allow private intermediate
transfers while applying required controls at issuance and redemption.

```text
controlled inventory admission
  -> controlled CWU issuance
  -> private bearer transfers
  -> controlled redemption or delivery
```

This endpoint model is a feature, but it must be described accurately. Wallet,
network, timing, denomination, and redemption metadata can still reveal
information.

## Required policy descriptor

A machine-readable CWU policy should include fields such as:

```json
{
  "instrument_class": "clear-warehouse-unit",
  "cmu": "cmu-<keyset-id>",
  "display_code": "CWU-WHEAT-CWRS-1-2026",
  "commodity": "wheat",
  "class": "Canada Western Red Spring",
  "grade": "No. 1",
  "production_period": "2026 crop year",
  "unit": {"amount": 1, "measure": "kilogram"},
  "eligible_locations": ["<approved warehouse network>"],
  "entitlement_type": "<defined legal claim>",
  "inventory_registry": "<authoritative registry>",
  "inspection_standard": "<standard and authority>",
  "redemption_methods": ["physical-delivery", "warehouse-receipt"],
  "minimum_delivery_amount": 20000,
  "charges_policy": "<published terms>",
  "expiry_policy": "<published terms>",
  "governing_law": "<jurisdiction>",
  "policy_version": "<version>"
}
```

The example is conceptual, not a finalized Clear schema. Exact terms should be
signed by the scheme authority and discoverable from the CMU descriptor.

## Metrics and reconciliation

Public supply figures should distinguish cryptographic state from inventory
evidence.

| Metric | Meaning |
| --- | --- |
| Issued CWU | Supply introduced under treasury authorization |
| Retired CWU | Supply permanently removed from circulation |
| Outstanding CWU | Issued minus retired under the CMU accounting policy |
| Eligible inventory | Quantity currently satisfying warehouse policy |
| Reserved inventory | Eligible quantity committed to outstanding CWU |
| Available minting capacity | Eligible unencumbered inventory not already reserved |
| Pending redemption | Validated claims awaiting external performance |
| Impaired inventory | Previously eligible quantity under exception or regrading |
| Reconciliation time | Time of the latest inventory-to-supply comparison |

Clear can calculate supply and proof-state diagnostics. Inventory quantities
must come from the warehouse or registry and should carry provenance, time,
and an attestation or signature. A dashboard must not present self-reported
inventory and mint-computed supply as if they were the same kind of evidence.

## Failure and shortfall policy

A credible CWU scheme must define what happens when the physical and digital
worlds diverge.

Possible events include:

- warehouse insolvency or delisting;
- theft, fire, flood, contamination, or spoilage;
- assay, grading, or weight error;
- duplicate pledge or undisclosed encumbrance;
- insurance lapse or rejected claim;
- mint-key compromise or inconsistent mint state;
- inventory registry outage;
- legal order preventing delivery;
- issuer insolvency; and
- outstanding supply exceeding eligible inventory.

The response may include issuance suspension, redemption-only status,
substitution, insurance proceeds, pro-rata allocation, conversion, migration,
or loss. Clear can enforce a lifecycle state and preserve evidence. It cannot
decide who bears the loss unless the governing policy gives an authorized body
that power.

## Regulatory characterization

A CWU could be characterized differently across jurisdictions and designs. It
might be treated as a warehouse receipt, document of title, commodity claim,
prepaid instrument, payment instrument, derivative, security, deposit-like
claim, or another regulated product.

The classification will depend on substance rather than branding, including:

- the holder's legal interest in the goods;
- whether delivery is expected or merely optional;
- whether the issuer promises cash value or investment return;
- transferability and marketing;
- the roles of the warehouse, issuer, and custodian;
- whether inventory is pooled or specifically allocated; and
- applicable commodity, warehouse, payments, securities, tax, and insolvency
  law.

The name **Clear Warehouse Unit** is deliberately descriptive without claiming
that the instrument is legally a warrant. A scheme should use **Clear Warrant
Unit** only where governing law and the operative documents actually give the
CMU that status.

## Recommended implementation sequence

### Phase 1: policy model and manual reconciliation

- Define the CWU policy descriptor and canonical naming rules.
- Use one CMU for one genuinely interchangeable inventory pool.
- Record warehouse attestations and approved minting capacity.
- Require treasurer authorization within that capacity.
- Reconcile inventory, issued supply, retired supply, and pending redemption.
- Operate redemption through a documented manual process.

### Phase 2: registry integration

- Add a signed inventory-capacity interface.
- Bind every capacity record to the exact CMU and policy version.
- Prevent issuance beyond unused capacity.
- Record impairment, release, and redemption states without exposing bearer
  proofs.
- Display source and freshness for inventory metrics.

### Phase 3: delivery orchestration

- Integrate warehouse, inspection, and delivery systems.
- Issue signed redemption receipts for external performance.
- Add controlled conversion between grades, locations, and production years.
- Define recovery and dispute procedures for partial or failed delivery.

### Phase 4: institutional recognition

- Establish the governing legal agreements and participant rules.
- Obtain jurisdiction-specific regulatory analysis.
- Add independent inventory and supply attestations.
- Define insolvency, shortfall, insurance, and loss-allocation treatment.

## Conclusion

The CWU concept gives Clear a credible bridge between coin-like circulation
and warehouse-controlled goods.

It works because the mint does not need to observe every transfer. The
institutional controls are concentrated at the endpoints: inventory admission
and issuance on one side, redemption and release on the other. Between those
points, holders can carry and transfer private bearer Mint Notes.

The precision comes from refusing to collapse unlike goods into one token.
Commodity, class, grade, production year, certification, location, measure,
and redemption rights can each determine the CMU boundary. One mint can host a
large catalogue while every pool remains distinct in authority, supply,
backing, lifecycle, and risk.

The durable formulation is:

> A Clear Warehouse Unit is a fungible bearer unit representing a
> policy-defined entitlement to a measured quantity of eligible inventory held
> within a recognized warehouse or custody system.

That definition is broad enough for metals and agricultural commodities, but
careful enough not to confuse a minted bearer unit with the warehouse,
inventory registry, legal warrant, or physical goods behind it.

