# Root CMU Issuance and Delivery

## Status

Implemented for local testing and interoperability work. This is not the
production treasurer authority model.

## Purpose

`clear-root` is the primary privileged bootstrap and development utility for a
Clear mint environment where the operator token and mint configuration are
available. It lets the mint operator issue, hold, export, send, retire, and
summarize test CMU denominated in the mint's active Clear Mint Unit.

The root CMU exists for deployment simplicity and mint reliability testing.
It behaves like other CMUs once issued, so it can be sent through wallets and
used to prove that issuance, transfer, swap, proof-state, retirement, metadata,
and recovery paths work end to end. Its main job is operational confidence
before and between formal treasury workflows. Ordinary community, venue, or
program currencies should move to treasurer-managed CMUs once the operator is
ready to delegate currency authority.

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
CLEAR_ROOT_API_URL=http://127.0.0.1:3340
CLEAR_CURRENCY_NAME="Clear Lab Credit Program"
CLEAR_MINT_TITLE="Clear Mint"
CLEAR_MINT_TAG_LINE="Privately issued community value."
CLEAR_CURRENCY_ALIAS="Clear Lab Credits"
CLEAR_CURRENCY_UNIT_ALIAS="credits"
CLEAR_ROOT_AUTHORITY_NPUB=npub...
CLEAR_ROOT_API_ALLOWED_NETWORKS=127.0.0.0/8,::1/128,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,fc00::/7
```

`CLEAR_MASTER_SECRET` derives the initial test keyset. If
`CLEAR_ROOT_AUTHORITY_NPUB` is configured, it represents the root operator
authority for this bootstrap mint and participates in key derivation. Changing
that root operator authority creates a different keyset and therefore a
different CMU. Existing databases are bound to the keyset identity they were
created with.

`CLEAR_OPERATOR_TOKEN` protects the FastAPI operator endpoints. `clear-root`
reads it from the privileged environment and sends it as the API authorization
value when issuing, retiring, or reading operator summaries.

Operator endpoints are additionally restricted by source network. With the
default loopback-only setting, they require a loopback client. If
`CLEAR_ROOT_API_LOOPBACK_ONLY=false` is used so another container can call the
operator API, Clear still limits access to `CLEAR_ROOT_API_ALLOWED_NETWORKS`.
Keep `/v1/operator/*` blocked at public reverse proxies.

Deployments that expose a public mint should prefer separate listeners. Run the
public listener with `clear --surface public` so operator routes are absent
from the proxy target. Run an internal-only listener for privileged tooling,
for example on port `3340`, and point `CLEAR_ROOT_API_URL` or wrapper tooling
at that internal URL. Mainstay uses this pattern with public `clear:3339` and
internal `clear-operator:3340`.

`CLEAR_MINT_URL` is the canonical public URL advertised by the mint and encoded
in circulating tokens. `CLEAR_ROOT_API_URL` is only the connection used by the
privileged root CLI. In Docker it points at the private operator listener, for
example `http://127.0.0.1:3340` inside the `clear-operator` container, allowing
the CLI to bypass the reverse proxy without placing that loopback address in
tokens. Outside Docker it defaults to `http://127.0.0.1:3339` and rejects
non-loopback addresses unless explicitly configured otherwise.

`CLEAR_MINT_TITLE` controls the public homepage title and defaults to
`Clear Mint`. `CLEAR_MINT_TAG_LINE` controls the homepage tagline and defaults
to `Privately issued community value.` `CLEAR_CURRENCY_ALIAS` and
`CLEAR_CURRENCY_UNIT_ALIAS` are startup defaults for wallet-facing display
metadata. They seed the legacy/root CMU label when the CMU keyset record is
first created or migrated, but they do not overwrite an existing CMU label
already persisted in the mint database. To rename a live CMU, update the CMU
record explicitly:

```sh
docker compose exec clear-operator clear-root cmu label cmu-<keyset-id-or-unit> \
  --name "Harbour Lab Credits" \
  --unit-alias "credits"
```

To hide an active CMU from the public home page without disabling it, mark it
private:

```sh
docker compose exec clear-operator clear-root cmu unlist cmu-<keyset-id-or-unit>
```

The authorized treasurer can also make the same signed request from the public
treasury surface:

```sh
poetry run clear-treasury --mint https://clear.example --nsec <treasurer-nsec> \
  cmu unlist --cmu-id cmu-<keyset-id>
```

Unlisted CMUs remain available through their exact CMU id or keyset id. They
are still returned by direct keyset endpoints and can still be issued,
accepted, redeemed, and inspected by software that already knows the id. To
list the CMU on the public home page again:

```sh
docker compose exec clear-operator clear-root cmu list cmu-<keyset-id-or-unit>
```

Treasurers use the matching signed command:

```sh
poetry run clear-treasury --mint https://clear.example --nsec <treasurer-nsec> \
  cmu list --cmu-id cmu-<keyset-id>
```

Wallets resolve the live label from `/v1/keysets`, `/v1/keys`, or
`/v1/keys/{keyset_id}` and continue to bind balances to the canonical mint,
CMU, and keyset identity.

By default, `clear-root send` requires the advertised `CLEAR_MINT_URL` to be a
well-formed public HTTPS route. It refuses an internal-only value such as
`http://clear:3339` before recipient discovery, proof export, or wallet
mutation. When the operator knows the recipient shares the same Mainstay mint,
internal delivery requires both an explicit acknowledgement and relay:

```sh
clear-root send 20 alice@example.com \
  --allow-internal-mint-delivery \
  --relay ws://spurline:8080
```

The override asserts mint reachability; `--relay` prevents the CLI from
silently using an externally advertised recipient route. Safebox Web remains
the preferred local transfer path because it can establish co-residency from
Mainstay's local handle directory. `clear-root withdraw` remains available for
deliberate manual token handling.

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
should use the generalized lifecycle and accounting term `retire`.

Redemption is the normal holder-initiated reason for retirement. Expiration,
revocation, cancellation, or reconciliation may also lead to retirement under
a future policy and enforcement model. The current command retires proofs that
are presented to it and records the optional `--memo`; it does not automatically
expire units, revoke unpresented bearer notes, or store a structured retirement
reason. Retirement does not imply an external payout.

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

Without the explicit internal-delivery override, this command is available
only when `/v1/info` advertises a public HTTPS `mint_url`. An internal-only mint
cannot establish that a remote recipient can reach its proof API, so delivery
fails before bearer proofs are prepared.

Delivery is not reported as successful merely because the relay publish call
returned. Clear republishes as needed and requires at least one configured
recipient relay to return the exact kind `1059` event by ID. Successful output
includes `publish.verified: true` and `publish.verified_relays`. If readback
cannot be verified, the command fails before removing the proofs from the root
wallet.

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
  "token": "cashuB...",
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

Acorn's private `home_relay` and its public receive route are deliberately
separate. The home relay is the wallet's current state context and may be
reachable only inside a Mainstay, local network, or private deployment. Remote
Clear senders should use the recipient's public NIP-05 relay hints, signed
inbox relays, or explicit public relay override.

Operators troubleshooting a missing Acorn receipt should first inspect the
recipient's public receive configuration:

```sh
poetry run acorn set --show-public-relays
poetry run acorn inbox-relays --json
```

If the Acorn moved contexts or the public relay changed, refresh the public
route and then rescan the receiving relays:

```sh
poetry run acorn inbox-relays wss://spurline.safebox.dev --json
poetry run acorn set --public-relays wss://spurline.safebox.dev
poetry run acorn receive-clear --preview --json
```

When the sender reports a published event ID, target it directly:

```sh
poetry run acorn receive-clear --event-id <event-id> --json
poetry run acorn clear accept <event-id> --json
```

A Safebox Web NIP-05 endpoint that advertises Clear receive support must list
externally reachable WebSocket relays. Context-local relays, Docker service
names, loopback addresses, and VPN-only routes are not suitable public receive
routes for remote treasury delivery.
