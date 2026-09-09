---
title: Transferability and Acceptance
description: Why a transferable Clear Mint Note is not automatically accepted or trusted.
---

# Transferability and Acceptance

A Clear Mint Note is designed to move between holders. That does not mean every
wallet can use it from every network, or that every person or organization has
agreed to accept it.

Clear keeps three questions separate:

1. **Where can it be transferred?**
2. **Will the recipient accept it?**
3. **Who stands behind it?**

## Transfer scope

A wallet can describe the current practical transfer scope in two simple ways.

<div class="clear-grid" markdown>

<article class="clear-card" markdown>

### Local only

Transferable between wallets using the same local services. Those wallets can
reach the same Clear mint and use a suitable local delivery path.

</article>

<article class="clear-card" markdown>

### Across networks

The mint and recipient provide routes intended to work outside one local
service environment. The receiving wallet still decides whether to accept the
CMU.

</article>

</div>

This scope is not permanently attached to the Mint Notes. A mint can add,
replace, or withdraw a route without changing its keyset, CMU, or outstanding
notes. Wallets derive the label from the routes available for a particular
transfer.

"Across networks" does not mean universally available or accepted. It means
only that usable transfer is not confined to one shared local service context.

## Acceptance is a separate decision

A recipient may accept a locally transferable CMU from a known community and
decline a cross-network CMU from an unfamiliar issuer. Technical validity and
reachability do not make that decision for them.

Acceptance may depend on:

- the organization or community standing behind the CMU;
- what the issuer promises to provide on redemption;
- the recipient's relationship with that issuer;
- any limits, expiry terms, or participating providers; and
- the recipient's own wallet or organizational policy.

Being served by the same mint installation does not make two CMUs equivalent.
They may have different keysets, treasurers, policies, liabilities, and circles
of recognition.

## Authority remains visible

The treasurer authorizes routine issuance and liability actions for a CMU under
its policy. The mint operator keeps the Clear service working. The service
identity establishes which mint is being reached. These are distinct roles.

A useful wallet presentation keeps them distinct too:

```text
Transfer scope: Across networks
Treasurer: Community Treasury
Recognition: Recognized locally
```

When recognition evidence is unavailable, the wallet should say so rather
than treating reachability as trust:

```text
Transfer scope: Across networks
Treasurer: Not verified
Recognition: Not established
```

## A familiar historical pattern

There is a limited parallel with the Florentine florin. It was issued by
Florence but became recognized for trade well beyond Florence. Issuance,
circulation, and voluntary acceptance were related without being identical.
The [British Museum Money Gallery guide](https://www.britishmuseum.org/sites/default/files/2021-05/Money_Gallery_LPG_2020_Room_68.pdf)
notes that the florin and Venetian ducat were recognized and trusted as trading
currencies throughout Europe.

Clear uses modern cryptographic bearer notes rather than precious-metal coins,
so the analogy should not be carried too far. The useful idea is that a unit
issued under one bounded authority can travel farther when other people choose
to recognize it. Wider circulation does not erase the identity or
responsibility of its issuer.

Read [How Clear Is Governed](governance.md) to understand the currency root,
mint operator, and treasurer roles, or [Mint Notes and CMU](mint-notes.md) for
the identifiers that keep different Clear balances separate.
