# CMU Transfer Request Design

Status: Proposed for the first release

## Summary

Clear should implement a transfer-request profile using Cashu NUT-18 Payment
Requests for Mint Notes denominated in a specific `cmu-<keyset-id>`. It should
not invent a new wire format. A compatible request retains the standard
`creqA` prefix, CBOR serialization, Base64URL encoding, payment payload, and
transport model.

NUT-18 uses *Payment Request* and *payment payload* as wire-protocol terms.
Clear product and wallet language calls the resulting CMU movement a
**transfer**, preserving the boundary that cash activity is presented as
payments while organization-issued CMUs are presented as transfers.

This profile still depends on custom-unit support. A generic NUT-18 wallet that
only recognizes units such as `sat` may reject a CMU request even though the
request encoding itself is valid. Clear, Acorn, and other compatible wallets
must explicitly advertise and test CMU support.

The principal Clear rule is:

```text
request.u = cmu-<keyset-id>
```

The receiving wallet creates the payment request instead of asking a Lightning
mint for a BOLT11 invoice. The sending wallet scans the request, selects Mint
Notes in the exact requested CMU, and sends a NUT-18 payment payload over the
requested transport.

## Initial profile

The first implementation uses these NUT-18 fields:

| Field | Clear use |
| --- | --- |
| `i` | Receiver-generated opaque payment ID |
| `a` | Requested amount in the CMU, net of input fees |
| `u` | Exact canonical `cmu-<keyset-id>` |
| `s` | `true` for a single-use request unless explicitly reusable |
| `m` | Strict list containing the accepted Clear mint endpoint |
| `mp` | `false` or omitted so the mint list is strict |
| `d` | Human-readable description shown before payment |
| `t` | One or more standard NUT-18 transports |
| `nut10` | Optional locking condition when required by the receiver |

`sm` is omitted in the first release. A Clear CMU transfer is a direct transfer
of Mint Notes in the requested CMU, not a request to melt another unit through
Lightning, on-chain payment, or another settlement method.

An example JSON representation before CBOR encoding is:

```json
{
  "i": "order-8f19c02a",
  "a": 64,
  "u": "cmu-00a1b2c3d4e5f6",
  "s": true,
  "m": ["https://clear.example"],
  "mp": false,
  "d": "Emergency food allocation",
  "t": [
    {
      "t": "post",
      "a": "https://wallet.example/payments/cashu"
    }
  ]
}
```

The encoded request remains:

```text
creqA + base64_urlsafe(CBOR(payment_request))
```

## Payment payload

The sender delivers the standard NUT-18 payment payload:

```json
{
  "id": "order-8f19c02a",
  "memo": "Payment",
  "mint": "https://clear.example",
  "unit": "cmu-00a1b2c3d4e5f6",
  "proofs": []
}
```

The request does not itself contain a Lightning invoice and does not require a
Lightning round trip.

## Receiver validation

Before accepting the transfer, the receiver must:

1. decode the request or payload using bounded input sizes;
2. match the payload `id` to an outstanding request when `i` was supplied;
3. require the payload `unit` to equal the request `u` exactly;
4. parse the keyset ID from `cmu-<keyset-id>` and require every proof `id` to
   match it;
5. require the payload mint to appear in the strict request mint list;
6. normalize and compare mint URLs without silently changing issuer identity;
7. calculate the received amount net of the keyset's NUT-02 input fees;
8. verify optional NUT-10 conditions;
9. validate and refresh the proofs with the issuing Clear mint; and
10. mark a single-use request complete only after the refresh succeeds.

Cryptographic signature validity alone is insufficient. The receiver must
also establish that the proofs have not already been spent. A transfer shown
as received but not yet refreshed should remain pending rather than final.

## Amount behavior

When `a` is present, the sender must provide proofs whose total value minus
input fees is at least the requested amount. Clear currently advertises zero
input fees, but the implementation must still calculate the amount using the
keyset metadata rather than hard-code that assumption.

When `a` is omitted, the request is open amount. The receiving application may
apply its own user-interface limits while preserving the NUT-18 encoding.

## Transport

The initial implementation may support:

- Nostr NIP-17 delivery using the standard NUT-18 `nostr` transport; and
- HTTPS POST using the standard `post` transport.

In-band delivery is also valid when the surrounding protocol defines how the
payment payload is carried. Transport protects delivery and routing but does
not replace proof validation.

## Mint clusters

The first release should put one canonical Clear endpoint in the strict mint
list. Mint clusters are deferred.

A future cluster-aware request may list several authenticated endpoints in
`m` when all of them serve the same logical mint, keyset, and CMU. The sender
still supplies one mint URL in the payment payload, and the receiver validates
it against the cluster manifest and strict mint list. Listing unrelated mints
that happen to display `CMU` is never acceptable.

## Security and privacy

- A transfer request is not proof that a transfer was accepted, an invoice
  settlement receipt, or issuer authorization.
- The receiver-generated ID must be unpredictable when it is used as a bearer
  lookup capability.
- Single-use completion state must be durable enough to reject replay.
- Descriptions are untrusted display text and must not be rendered as HTML.
- Wallets must visibly identify the logical mint and complete CMU before the
  sender confirms the transfer.
- Nostr or HTTPS metadata may reveal participants, timing, or amounts even when
  the Mint Notes themselves use blinded signatures.
- Proofs are bearer instruments and must not be logged or placed in URLs.

## Implementation boundary

The Clear mint must expose correct keyset, CMU, input-fee, swap, and proof-state
information. Request generation, QR presentation, transport, receipt tracking,
and finalization belong primarily in a wallet such as Acorn or a Safebox Web
application.

The Clear repository may provide shared typed models and codec functions so
wallet implementations do not create incompatible encodings. Those helpers
must remain independent from server configuration and keyset secrets.

## First-release acceptance tests

- encode and decode the official NUT-18 field structure without loss;
- reject malformed prefix, Base64URL, CBOR, field types, and oversized input;
- generate a request for an exact `cmu-<keyset-id>`;
- reject a payload with a different unit, proof keyset ID, or strict mint;
- accept and refresh a valid transfer from the requested CMU;
- enforce fixed and open amounts, including input-fee calculation;
- enforce single-use request replay protection; and
- round-trip requests through QR text, Nostr transport, and HTTPS POST fixtures.

## Reference

- [Cashu NUT-18: Payment Requests](https://github.com/cashubtc/nuts/blob/main/18.md)
