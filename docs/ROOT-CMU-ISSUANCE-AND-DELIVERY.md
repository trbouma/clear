# Root CMU Issuance and Delivery

## Status

Implemented for local testing and interoperability work. This is not the
production treasurer authority model.

## Purpose

`clear-root` is the primary privileged bootstrap and development utility for a
Clear mint environment where the operator token and mint configuration are
available. It lets the mint operator issue, hold, export, send, retire, and
summarize test CMU denominated in the mint's active Clear Mint Unit.

The active unit is the keyset-bound protocol unit:

```text
cmu-<keyset-id>
```

Friendly names such as "Harbour Lab Credits" and friendly unit aliases such as
"smiles" are display hints only. Wallets must still identify balances by mint,
CMU, and keyset id.

## Environment

The local mint requires:

```sh
CLEAR_MASTER_SECRET=<32-byte secret, commonly 64 hex chars>
CLEAR_OPERATOR_TOKEN=<operator API bearer token>
CLEAR_DATABASE=./data/clear.sqlite3
CLEAR_MINT_URL=http://127.0.0.1:3339
CLEAR_ROOT_API_URL=http://127.0.0.1:3339
CLEAR_CURRENCY_NAME="Clear Lab Credit Program"
CLEAR_CURRENCY_ALIAS="Clear Lab Credits"
CLEAR_CURRENCY_UNIT_ALIAS="credits"
CLEAR_ROOT_AUTHORITY_NPUB=npub...
```

`CLEAR_MASTER_SECRET` derives the initial test keyset. If
`CLEAR_ROOT_AUTHORITY_NPUB` is configured, it participates in key derivation, so
changing the root authority creates a different keyset and therefore a
different CMU. Existing databases are bound to the keyset identity they were
created with.

`CLEAR_OPERATOR_TOKEN` protects the FastAPI operator endpoints. `clear-root`
reads it from the privileged environment and sends it as the API authorization
value when issuing, retiring, or reading operator summaries.

`CLEAR_MINT_URL` is the canonical public URL advertised by the mint and encoded
in circulating tokens. `CLEAR_ROOT_API_URL` is only the connection used by the
privileged root CLI. In Docker it remains `http://127.0.0.1:3339`, allowing the
CLI to bypass the reverse proxy without placing that loopback address in
tokens. Outside Docker it defaults to `http://127.0.0.1:3339` and rejects
non-loopback addresses.

## Commissioning direction

The commands in this guide let the root exercise the current mint manually.
Before remote treasurer access is implemented, `clear-root` will add a formal
`verify` workflow, durable readiness evidence, and an explicit treasury enable
gate. The verification will use the same action layer as treasurer requests so
the root proves the path that will actually be delegated.

See
[Root Commissioning and Treasury Readiness](ROOT-COMMISSIONING-AND-TREASURY-READINESS-DESIGN.md)
for the accepted design.

## Running the mint

```sh
poetry run clear --host 127.0.0.1 --port 3339
```

Useful inspection endpoints:

```text
GET /
GET /health
GET /v1/info
GET /v1/keys
GET /docs
```

`/v1/info` exposes the canonical protocol unit plus wallet-facing aliases:

```json
{
  "mint_url": "https://clear.example",
  "currency": {
    "name": "Clear Lab Credit Program",
    "display_unit": "CMU",
    "unit": "cmu-00ce29eeaf094301",
    "protocol_unit": "cmu-00ce29eeaf094301",
    "friendly_alias": "Clear Lab Credits",
    "friendly_unit_alias": "credits"
  }
}
```

## Issuance and the local root wallet

`clear-root issue 25` authorizes and issues 25 CMU into circulation. Cashu
proofs are the technical representation of those issued units; a Cashu token
is an optional transport encoding.

By default, the command stores the issued proofs in a local JSON wallet:

```text
data/clear-root-wallet.json
```

This wallet is an operator-side convenience for testing. It is not the Acorn
wallet and it is not a production treasury ledger. Ordinary issuance output
does not print the bearer token or raw proofs after they are stored.

Issue 25 CMU into the local root wallet:

```sh
poetry run clear-root issue 25 --memo "test CMU"
```

Issue 25 CMU and immediately encode its proofs as a Cashu token:

```sh
poetry run clear-root issue 25 --memo "test CMU" --to-token
```

Export and withdraw are synonyms. They select proofs from the local root wallet
and encode them into a Cashu token:

```sh
poetry run clear-root withdraw 25 --memo "disbursement"
poetry run clear-root export 25 --memo "disbursement"
```

If the wallet cannot represent the requested amount exactly, `clear-root send`
can swap a larger proof at the mint, keep the change in the root wallet, and
deliver the requested amount.

## Retirement

`clear-root retire` permanently removes CMU from circulation. Retire an amount
held by the local root wallet:

```sh
poetry run clear-root retire 25 --memo "program completed"
```

Retire a Cashu token supplied on stdin:

```sh
printf '%s' "$token" | poetry run clear-root retire --memo "returned units"
```

Raw proofs may be supplied as a JSON list, or as an object containing `unit`
and `proofs`, through stdin or a file:

```sh
poetry run clear-root retire --proofs-file returned-proofs.json
```

The mint validates the proofs, marks them spent, and records the retired CMU.
`redeem` remains a compatibility alias for `retire`; new operator workflows
should use the accounting term `retire`. Retirement does not imply an external
payout.

## Supply summary

```sh
poetry run clear-root info
poetry run clear-root summary
```

The summary reports:

```text
issued
retired
circulating
outstanding
```

Circulating means issued minus retired in the Clear mint accounting store.
`outstanding` is retained as a compatibility alias for the same amount. Neither
field means every Mint Note is currently held by a reachable wallet.

## NIP-05 delivery

`clear-root send` delivers Clear tokens to a NIP-05 or Lightning-style address
that advertises Clear support:

```sh
poetry run clear-root send 25 trbouma@acorn.safebox.dev --memo "test CMU"
```

The delivery format is:

```text
outer relay-visible event: kind 1059
inner Clear transfer: kind 7379
protocol tag: clear-token-transfer
transport: nip59
```

The encrypted inner payload is a JSON object:

```json
{
  "type": "clear-token",
  "version": 1,
  "token": "cashuA...",
  "mint": "http://127.0.0.1:3339",
  "unit": "cmu-00ce29eeaf094301",
  "amount": 25,
  "keyset_ids": ["00ce29eeaf094301"],
  "memo": "test CMU"
}
```

Sender identity is ephemeral by default. If `CLEAR_ROOT_NSEC` or `--nsec` is
supplied, that key signs the inner event; otherwise `clear-root` generates an
ephemeral sender key for the transfer.

## Receiver advertisement

A compatible NIP-05 provider advertises Clear receive support in the
well-known response:

```json
{
  "clear": {
    "alice": {
      "protocols": ["clear-token-transfer"],
      "transports": ["nip59"],
      "kinds": [7379]
    }
  }
}
```

Optional `mints` and `units` arrays restrict what the receiver claims to
accept. When those arrays are omitted or empty, the receiver advertises general
Clear support and validates the mint, CMU, and keyset from the encrypted
payload after receipt.

## Relationship to Acorn

Acorn receives kind `7379` Clear transfers through a separate pending Clear
receipt path. Clear tokens are not merged into Acorn's normal sats proof state
and are not counted in the sats balance.
