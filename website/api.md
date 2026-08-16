---
title: API
description: Initial Cashu and operator endpoints exposed by Clear.
---

# API

!!! note "Initial API"
    These are the endpoints in the current prototype. The operator boundary is
    temporary. Signed treasurer instructions and locally installed,
    root-signed policy events will replace it as the governance implementation
    develops.

## Public service

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Clear service, keyset, and unit metadata |
| `GET` | `/health` | Process health |
| `GET` | `/v1/info` | Cashu mint capabilities |
| `GET` | `/v1/keys` | Active keyset and public keys |
| `GET` | `/v1/keys/{id}` | Public keys for one keyset |
| `GET` | `/v1/keysets` | Keyset metadata |
| `POST` | `/v1/mint/quote/clear` | Request an issuance quote |
| `GET` | `/v1/mint/quote/clear/{id}` | Read quote authorization and issuance totals |
| `POST` | `/v1/mint/clear` | Exchange an authorized quote for blind signatures |
| `POST` | `/v1/swap` | Atomically exchange proofs for new blind signatures |
| `POST` | `/v1/checkstate` | Check whether proof secrets are unspent or spent |

## Prototype operator boundary

These endpoints require `Authorization: Bearer <CLEAR_OPERATOR_TOKEN>`.

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/v1/operator/quotes/{id}/authorize` | Authorize the full requested amount |
| `POST` | `/v1/operator/retire` | Validate and permanently retire proofs |
| `GET` | `/v1/operator/summary` | Read issued, retired, and outstanding supply |

The interactive OpenAPI description is available at `/docs` while the service
is running.

The current `/v1/info` response also includes Clear's `currency` metadata:
friendly name, display unit, keyset-bound protocol unit, public-key
fingerprint, and NUT-02 keyset ID. Applications should resolve the friendly
name from this metadata while retaining the logical mint, complete protocol
unit, and authenticated service endpoints as the balance identity and routes.

The target protocol unit is `cmu-<keyset-id>`. The current implementation may
still return a legacy `PTS` or `pts` value until the code and database migration
is completed. Endpoint names and Cashu fields that use *proof* retain that
technical meaning: a Cashu proof is the encoded spendable representation of a
Mint Note.
