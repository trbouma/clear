---
title: How Clear Is Governed
description: How currency authorities, mint operators, and treasurers share responsibility in Clear.
---

# How Clear Is Governed

A Clear currency belongs to the organization or community that defines it. The
software keeps proofs valid and prevents double spending, but it does not get
to appoint the people who control the currency.

Clear separates that responsibility into three roles: one establishes the
rules, one operates the infrastructure, and one carries out routine treasury
decisions.

<div class="clear-grid" markdown>

<article class="clear-card" markdown>

### Currency root authority

Establishes the currency and appoints its treasurers. It approves infrequent
governance changes using an offline or hardware-protected root key.

</article>

<article class="clear-card" markdown>

### Mint operator

Runs Clear, protects its database, maintains relay connections, installs
approved policies, and keeps the service available. Operating the server does
not confer authority to issue Mint Notes.

</article>

<article class="clear-card" markdown>

### Treasurers

Authorize routine Mint Note issuance, redemption, and retirement within the
limits of the active policy. A policy can require one treasurer or approval
from several.

</article>

</div>

## When a treasurer also controls a keyset

Ordinarily, a treasurer holds an authorization key and the operational signer
holds the keyset secret. A policy can deliberately combine those
responsibilities by appointing a treasurer as a keyset custodian or delegated
signer.

That custodian can bring an existing keyset to a Clear operator. The operator
must approve its enrollment before the deployment advertises the CMU, records
its issuance, or commits to redeeming its Mint Notes. This makes keysets
portable without allowing a hosting operator to appoint itself as issuer.

Possession of the raw keyset secret nevertheless means the custodian can create
cryptographically valid Mint Notes. Operator approval cannot undo that fact; it
governs whether the service recognizes and accounts for the issuance. Where
both parties must approve every issuance, the secret should remain in a policy-
enforcing HSM or remote signer that requires both approvals before signing.

## Why separate the roles?

Each role carries a different kind of responsibility.

- The **root authority** decides who is trusted to act.
- The **mint operator** keeps the infrastructure working.
- The **treasurers** make day-to-day supply decisions.
- The **mint** verifies those decisions and issues Mint Notes by signing blinded
  Cashu outputs.

Compromising an ordinary treasurer should not allow someone to appoint new
treasurers. Running the mint should not let an operator rewrite the currency's
governance. The root key should not be exposed to a continuously running
internet service.

One person can fill more than one role in a small organization. Clear still
uses separate keys for each role, making it possible to divide responsibilities
later without creating a new currency.

## How issuance works

An authorized treasurer uses the separately installable Clear Treasury CLI to
request an issuance:

1. The Treasury CLI creates new note secrets and blinded outputs locally.
2. The treasurer signs an authorization naming the CMU, amount, purpose, policy
   version, and exact issuance request.
3. Clear confirms that the signer is an authorized treasurer and that the
   request satisfies the current policy.
4. The mint signs the blinded outputs and records the supply change.
5. The Treasury CLI unblinds the response and returns a Cashu token containing
   the issued Mint Notes.

Clear never needs the treasurer's private key, and the mint never learns the
final bearer note secrets.

## Mint clusters

The same keyset and CMU may be served by a **mint cluster**, allowing an
authorized treasurer to issue through different mint instances. The treasurer
selects the proposed members under the active policy, and each mint operator
approves its instance's participation.

The signed cluster configuration tells every member which other mints it must
consult before accepting a note. Members require strongly consistent issuance,
authorization, and spent-note state. A mint-to-mint reserve-and-commit protocol
can coordinate that decision when the instances do not share one database.
Periodic synchronization is useful for recovery but cannot prevent two mints
from accepting the same note at the same time.

Independent mint instances must use independent keysets and therefore distinct
CMUs. A shared operator, treasurer, name, or governance root does not merge
their balances.

```text
Root authority appoints treasurers
                 |
                 v
Treasurer signs an issuance request
                 |
                 v
Clear verifies policy and signs blinded outputs
                 |
                 v
Treasury CLI returns a transferable token
```

## Changing a treasurer

Treasurer replacement should be easy to perform correctly, but difficult to do
accidentally. Clear uses a deliberate policy-change process:

1. Prepare a successor policy containing the replacement public key.
2. Confirm that the new treasurer controls the corresponding private key.
3. Have the currency root authority sign the policy as a Nostr event.
4. Install the signed event on the mint and restart Clear.
5. Confirm the new policy version and event ID.

The mint operator can install a policy but cannot forge the root authority's
signature. Once activated, the old treasurer key loses authority immediately.
Earlier completed transactions remain verifiable under the historical policy.

## Local policy, optional transparency

The complete signed policy is installed locally, preserved in the currency
ledger, and backed up. Clear never activates a policy merely because it appears
on a relay.

An organization may publish a policy commitment or public service record so
others can verify which policy is active. It may also mirror the complete
policy to a private relay or Spurline instance for continuity. Publishing the
treasurer list and its detailed scopes remains an explicit organizational
choice.

## What a holder should know

Before accepting a Clear currency, a holder should be able to identify:

- the organization or community standing behind it;
- its exact Clear Mint Unit, such as `cmu-<keyset-id>`;
- the logical mint, its authorized service endpoints, and issuing keyset;
- the policy describing what the Mint Notes represent; and
- any limits on use, retirement, conversion, or expiry.

Two programs may both display `CMU`, but their complete CMU identifiers and
logical mints remain separate promises with separate governance and risk.
Clear never combines them into one balance.

This separation is less novel than it may first appear. Read
[Old Function, New Tools](old-function-new-tools.md) for the connection to
ancient administrative records, corporate treasury, and Boards of Internal
Economy.

!!! note "Designed first, implemented carefully"
    This page describes Clear's target governance model. The current prototype
    still uses a simpler single-operator authorization mechanism. Signed policy
    events, the Treasury CLI, and multi-party approvals are planned milestones,
    not production-ready features.
