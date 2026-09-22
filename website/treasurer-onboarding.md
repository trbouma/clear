# Onboarding a Treasurer

This page gives the first-release operator flow for adding one treasurer and
creating one or more treasurer-authorized Clear Mint Units (CMUs).

The authority rule is:

```text
one active treasurer npub -> one or more CMUs
one CMU -> one active treasurer npub
```

The treasurer gives the mint operator an `npub`. The matching `nsec` stays with
the treasurer.

## 1. Confirm the Mint

Run privileged operator commands inside the Clear container:

```bash
docker compose exec clear-operator clear-root info
docker compose exec clear-operator clear-root cmu list
```

`clear-root` uses the loopback operator API and is not a remote treasurer
tool.

## 2. Get the Treasurer npub

The treasurer provides:

```text
npub1...
```

Do not put the treasurer's `nsec` in `.env`, deployment notes, logs, database
exports, API requests, or `clear-root` commands.

For development only, the container includes a helper that prints a keypair and
stores nothing:

```bash
docker compose exec clear-operator clear-root treasurer keygen
```

In separated custody, the treasurer should generate and keep their own `nsec`.

## 3. Add the Treasurer

```bash
docker compose exec clear-operator clear-root treasurer add npub1...
docker compose exec clear-operator clear-root treasurer list
```

Adding the treasurer records a public key. It does not create a CMU or issue
Mint Notes.

## 4. Grant One CMU Creation

```bash
docker compose exec clear-operator clear-root treasurer grant npub1...
docker compose exec clear-operator clear-root treasurer grants
```

The response includes the grant `id` and public `mint_url`, ready to share with
the treasurer. Both fields are also returned by `treasurer grants`.
A first-release grant is single-use and intended to
produce one keyset and one CMU. After it is consumed, the same treasurer may
receive another grant for another CMU.

## 5. Send the Grant Out of Band

To replace an unused grant, first revoke it as the operator:

```bash
docker compose exec clear-operator clear-root treasurer revoke-grant <grant-id>
docker compose exec clear-operator clear-root treasurer grant npub1...
```

Only pending grants can be revoked. The grant remains in `treasurer grants`
with status `revoked` and an audit record; it can no longer create a CMU.
Consumed grants cannot be revoked. Existing CMUs and notes are unaffected.

Give the treasurer:

- the mint URL, for example `https://clear.safebox.dev`; and
- the grant ID.

Do not give the treasurer `CLEAR_OPERATOR_TOKEN`, `CLEAR_MASTER_SECRET`, the
mint database, or keyset secrets.

## 6. Treasurer Creates the CMU

For an interactive handoff, save the single grant response as `grant.json` and run:

```bash
poetry run clear-treasury cmu create --grant-file grant.json
```

The file is read without modifying or deleting it. The grant is consumed at the
mint only after successful CMU creation. Piped JSON is also supported:

```bash
cat grant.json | poetry run clear-treasury cmu create --grant-stdin
```

The CLI reads `mint_url`, `id`, and `npub` from the grant. It displays the mint
and treasurer, prompts for the `nsec` with hidden input (unless supplied through
`--nsec` or `CLEAR_TREASURER_NSEC`), then asks for the CMU name and unit label.
The secret stays local; only a signed request is sent to the mint. The key must
match the grant's `npub`. Prompts use the controlling terminal, so stdin remains
available for the piped JSON. A terminal is required for this interactive mode.
Optional `--name` and `--unit-alias` values skip their respective prompts.

For a local operator-to-treasurer pipeline, disable the Docker TTY:

```bash
docker compose exec -T clear-operator clear-root treasurer grant "$TREASURER_NPUB" \
  | poetry run clear-treasury cmu create --grant-stdin
```

Cancelling during the prompts leaves the grant pending; it can be reused or revoked. For automation
without an interactive terminal, use the explicit command below.

The treasurer consumes the grant with their `nsec`:

```bash
clear-treasury --mint https://clear.safebox.dev \
  --nsec nsec1... \
  cmu create <grant-id> \
  --name "Gym Guest Passes" \
  --unit-alias "passes"
```

Or with the key in the environment:

```bash
export CLEAR_TREASURER_NSEC=nsec1...
clear-treasury --mint https://clear.safebox.dev \
  cmu create <grant-id> \
  --name "Gym Guest Passes" \
  --unit-alias "passes"
```

At creation time, the treasurer may choose `--name` and `--unit-alias` as
display hints for the CMU they are authorized to create. Wallets still bind
balances to the mint URL, canonical `cmu-<keyset-id>` unit, and keyset ID.

After the CMU exists, display metadata changes are operator-mediated. The
treasurer requests the change out of band, and the mint operator applies it:

```bash
docker compose exec clear-operator clear-root cmu label cmu-<keyset-id> \
  --name "Food Share Credits" \
  --unit-alias "shares"
```

The first argument can be the canonical CMU unit or the raw keyset ID. Label
changes do not change the keyset, CMU, ledger, treasurer authority, existing
Mint Notes, or holder balances.

The CLI signs the request. The mint verifies the treasurer key, mint URL,
grant, and replay nonce before generating and encrypting the new keyset secret.

## 7. Treasurer Confirms the CMU

The treasurer can ask the mint which active CMU is bound to their key:

```bash
clear-treasury --mint https://clear.safebox.dev \
  --nsec nsec1... \
  cmu info \
  --cmu-id <cmu-id>
```

Or, with `CLEAR_TREASURER_NSEC` already exported:

```bash
clear-treasury --mint https://clear.safebox.dev \
  cmu info \
  --cmu-id <cmu-id>
```

This is a signed read-only request. The mint returns the requested active CMU
only if that treasurer key controls the named unit. `--keyset-id <keyset-id>` is
also accepted when the treasurer wants to name the underlying keyset directly.

## 8. Choose Home Page Listing

By default, an active CMU appears on the mint home page. To hide it from the
home page without disabling direct use by CMU id:

```bash
clear-treasury --mint https://clear.safebox.dev \
  --nsec nsec1... \
  cmu unlist \
  --cmu-id <cmu-id>
```

To show it again:

```bash
clear-treasury --mint https://clear.safebox.dev \
  --nsec nsec1... \
  cmu list \
  --cmu-id <cmu-id>
```

The mint operator can also list or unlist any hosted CMU through `clear-root`.
A treasurer can only change visibility for CMUs controlled by their key.

Both listed and unlisted CMUs are accessible at `/cmus/<cmu-id>`; existing
`/cmus/<keyset-id>` links also work. Unlisting does not restrict access to the
description, supply, or treasurer details.

For operators, `clear-root cmu list <cmu-id>` lists the CMU on the home page;
`clear-root cmu list` without an ID still returns all CMU records.
The previous `private` and `publish` commands remain compatibility aliases.

## 9. Operator Verifies the CMU

The operator checks the consumed grant and the created CMU:

```bash
docker compose exec clear-operator clear-root treasurer grants
docker compose exec clear-operator clear-root cmu list
```

The CMU should also appear in public key discovery:

```bash
curl https://clear.safebox.dev/v1/keysets
curl https://clear.safebox.dev/v1/keys
```

Record the treasurer `npub`, grant ID, CMU name, `cmu-<keyset-id>` unit,
keyset ID, onboarding date, and out-of-band authorization reference.

## Operator Fallback

For development or controlled local bootstrap, the operator can consume a
grant from inside the container:

```bash
docker compose exec clear-operator clear-root cmu create <grant-id> \
  --name "Gym Guest Passes" \
  --unit-alias "passes"
```

Prefer the `clear-treasury` flow when the operator and treasurer are meant to
be separate. The signed flow proves that the treasurer controls the `nsec`.

## Safety Checks

These failures are expected:

- adding an `nsec` instead of an `npub` is rejected;
- consuming a grant with the wrong key is rejected;
- consuming a grant twice is rejected;
- signing for a different mint URL is rejected;
- creating another grant for the same active treasurer while an unused grant is
  still pending is rejected; and
- `clear-root` refuses non-loopback operator API URLs.

## 9. Treasurer Issues Mint Notes

After onboarding, the treasurer can issue Mint Notes for their CMU:

```bash
clear-treasury --mint https://clear.safebox.dev \
  --nsec nsec1... \
  issue 25 \
  --cmu-id <cmu-id> \
  --memo "Workshop credits"
```

By default, issued proofs are stored in a local treasurer wallet. The wallet
path is derived from the mint URL and treasurer `npub`:

```text
~/.clear/treasury-wallets/<mint-host>-<mint-hash>/<treasurer-npub>.json
```

Different `nsec`s and different mints therefore get different wallet files.
The path can be overridden with `--wallet` or `CLEAR_TREASURY_WALLET`.

Check the local wallet with:

```bash
clear-treasury --mint https://clear.safebox.dev \
  --nsec nsec1... \
  wallet balance
```

To issue directly to a token instead of the local wallet:

```bash
clear-treasury --mint https://clear.safebox.dev \
  --nsec nsec1... \
  issue 25 \
  --cmu-id <cmu-id> \
  --memo "Workshop credits" \
  --to-token
```

The treasurer can send an exact amount from the local wallet to a compatible
NIP-05 address or `npub`:

```bash
clear-treasury --mint https://clear.safebox.dev \
  --nsec nsec1... \
  send 10 alice@example.com \
  --cmu-id <cmu-id> \
  --memo "Guest pass"
```

If exact proofs are not available, `send` refreshes a larger proof through
`/v1/swap`, delivers the requested amount, and stores the change back in the
same treasurer wallet.

Delivery uses an ephemeral Nostr sender key by default. The treasurer `nsec`
authorizes treasury actions and selects the local wallet; it is not reused as
the delivery sender key.

## 10. Check Recipient Receive Routes

Clear delivery uses the recipient's public receive route. It must not depend on
a private or context-local home relay that remote senders cannot reach.

For an Acorn recipient, inspect the advertised route:

```bash
poetry run acorn set --show-public-relays
poetry run acorn inbox-relays --json
```

If the Acorn moved to a new context or the public relay changed, refresh the
public route from the receiving wallet:

```bash
poetry run acorn inbox-relays wss://spurline.safebox.dev --json
poetry run acorn set --public-relays wss://spurline.safebox.dev
```

Then scan or accept the transfer:

```bash
poetry run acorn receive-clear --preview --json
poetry run acorn receive-clear --event-id <event-id> --json
poetry run acorn clear accept <event-id> --json
poetry run acorn clear balances --json
```

For Safebox Web, the NIP-05 external relay list should contain public WebSocket
relay URLs. Do not advertise Docker service names, loopback URLs, VPN-only
routes, or other context-local home relays as the recipient's public Clear
delivery route.

Remote treasurer retirement is follow-on work.

## Describe a CMU

After creating a CMU, its owning treasurer can set the public description
beneath the title on the individual CMU page. Describe its purpose, where it is accepted,
and what holders can expect. Use the usual configured treasurer credentials:

```sh
poetry run clear-treasury --mint https://clear.safebox.dev cmu describe \
  --cmu-id cmu-YOUR-ID \
  --description "Community meal credits, accepted at participating kitchens."
```

For longer text, replace `--description` with `--description-file description.txt`.
Files are UTF-8. Plain text and paragraph breaks are supported, up to 10,000
characters; HTML and Markdown are not rendered. Use `--clear` to remove the text.
Treasury commands require an explicit `--cmu-id` or `--keyset-id`.

The operator can independently update any hosted CMU:

```sh
docker compose exec clear-operator clear-root cmu describe cmu-YOUR-ID \
  --description "Community meal credits, accepted at participating kitchens."
```

When using `--description-file` inside Docker, the file must be available inside
the container. Both update paths are audited. Existing CMUs start with an empty
description after the automatic database migration. Description changes do not
alter identity, supply, or listing visibility. An unlisted CMU's description is
still visible on its direct page; do not put secrets in it.
