---
title: CMU Payment Requests
description: Receiver-created payment requests for Mint Notes in one exact CMU.
---

# CMU Payment Requests

A Clear payment does not need to begin with a Lightning invoice. The receiving
wallet can create a Cashu NUT-18 payment request for a particular Clear Mint Unit:

```text
cmu-<keyset-id>
```

The sender scans the request and transfers Mint Notes from that exact CMU. The
receiver then validates and refreshes the notes with their issuing mint.

```text
Receiver creates request
        |
        v
  creqA... QR code
        |
        v
Sender selects requested CMU
        |
        v
Sender delivers Mint Notes
        |
        v
Receiver refreshes and finalizes
```

## A NUT-18 profile, not a new format

Clear retains the standard NUT-18 encoding and fields. The request places the
complete `cmu-<keyset-id>` in its unit field and the accepted Clear endpoint in
a strict mint list. It can request a fixed amount or leave the amount open.

Wallets must explicitly support custom CMU units. A wallet limited to `sat` or
other familiar units may correctly decode the request but still decline it.

The request may be delivered as a QR code and the resulting payment payload
may travel through HTTPS POST, Nostr NIP-17, or an in-band protocol.

## What the receiver checks

The receiving wallet checks that:

- the payload matches the request ID;
- the unit is the exact requested CMU;
- every proof names the keyset encoded in the CMU;
- the mint is in the strict accepted-mint list;
- the value covers the amount after input fees; and
- the mint confirms the proofs are unspent by successfully refreshing them.

A payment remains pending until the proofs have been validated and refreshed.
The payment request itself is not proof of payment.

## Release boundary

The first release uses one Clear endpoint in the strict mint list. A future
mint-cluster version may list several endpoints only when they serve the same
logical mint, keyset, and CMU.

The detailed design and acceptance tests are maintained in the
[CMU Payment Request design](https://github.com/trbouma/clear/blob/main/docs/CMU-PAYMENT-REQUEST-DESIGN.md).
