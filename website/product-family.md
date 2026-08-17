---
title: Product Family
description: How Clear fits with Safebox Web, Acorn, Grove, Spurline, Mainstay, and Lockbox.
---

# Product Family

Clear is a sibling service, not the wallet or the unified application.

It follows the shared principle **good boundaries, not barriers**. Clear keeps
its mint, currency, and governance boundaries explicit while standard Cashu
and Nostr interfaces allow wallets, applications, and local infrastructure to
work with it.

```text
                         Mainstay
                 unified local-first app
                            |
          +-----------------+-----------------+
          |                 |                 |
    Safebox Web          Acorn             Clear
      user flows     portable state    Mint Note issuer
                            |
                      +-----+-----+
                      |           |
                  Spurline      Grove
                  events        blobs

                Lockbox runs the stack locally
```

Acorn can hold Bitcoin- and Lightning-backed ecash as a Cash Balance while also
holding Mint Notes from multiple Clear CMUs and keeping every Clear balance
distinct. Safebox Web and Mainstay can present the issuer, policy, keyset, CMU,
confirmed state, and pending state in plain language.
Spurline can preserve wallet state and signed policy records. Grove can
preserve supporting policy documents or evidence.

Clear adds an issuance boundary to the family. It does not become a global
source of authority: each organization remains responsible for its own policy,
key custody, governance, and recognition.

## Local economies inside Mainstay

Clear gives Mainstay and Lockbox an optional local-first mint that works
alongside their Bitcoin, Lightning, and ecash payment capabilities. A church,
food-bank network, community association, campus, event, small resort, or
cruise ship can define a bounded credit recognized by participating people and
service providers. Wallets can keep broadly transferable sat-denominated funds
in a singular Cash Balance while displaying each issuer-defined credit under
plural Clear Balances.

That creates a different continuity path from externally issued Cashu ecash.
If an external mint is unavailable, Acorn may preserve received Mint Notes as
pending until it can confirm their proofs. If a Clear mint is running locally
on the organization's network, it can continue validating, swapping, issuing,
redeeming, and retiring its own Mint Notes without contacting Lightning or the
wider internet.

A resort or cruise ship, for example, could issue guest credits, staff
allowances, activity vouchers, meal credits, or emergency value through a
locally operated Clear mint. Shops and services on the local network recognize
that specific currency, while the operator's treasury governs issuance and
provider settlement. Mainstay supplies a coherent user experience, Acorn holds
the Mint Notes, Spurline carries local signed events, and Lockbox can host the
complete local runtime.

Clear currencies remain voluntary, limited-recognition instruments rather than
legal tender. They extend the family from payment continuity into local
economic coordination without requiring every Mainstay or Lockbox deployment
to operate a mint.
