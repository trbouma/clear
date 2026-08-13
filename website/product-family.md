---
title: Product Family
description: How Clear fits with Safebox, Acorn, Grove, Spurline, Mainstay, and Lockbox.
---

# Product Family

Clear is a sibling service, not the wallet or the unified application.

```text
                         Mainstay
                 unified local-first app
                            |
          +-----------------+-----------------+
          |                 |                 |
       Safebox            Acorn             Clear
      user flows     portable state     points mint
                            |
                      +-----+-----+
                      |           |
                  Spurline      Grove
                  events        blobs

                Lockbox runs the stack locally
```

Acorn can eventually hold multiple Clear currencies while keeping every
balance distinct. Safebox and Mainstay can present the issuer, policy, keyset,
confirmed state, and pending state in plain language. Spurline can preserve
wallet state and signed policy records. Grove can preserve supporting policy
documents or evidence.

Clear adds an issuance boundary to the family. It does not become a global
source of authority: each organization remains responsible for its own policy,
key custody, governance, and recognition.
