# Treasurer Onboarding Runbook

Status: First-release operator procedure

This runbook describes the step-by-step flow for onboarding one treasurer to
one or more Clear Mint Units (CMUs).

The first-release authority rule is:

```text
one active treasurer npub -> one or more CMUs
one CMU -> one active treasurer npub
```

The treasurer's `nsec` must stay with the treasurer. The mint operator stores
only the treasurer's `npub`.

Onboarding a treasurer is an infrastructure and authorization ceremony, not an
endorsement of the treasurer's program. The mint operator provides the Clear
service, protects operational key material, records the treasurer public key,
and enforces protocol checks. The treasurer, or the issuer represented by that
treasurer, remains responsible for issuance policy, supply discipline,
redemption terms, holder communications, and any real-world obligation attached
to the CMU.

## Preconditions

Before onboarding a treasurer:

- the Clear mint is running;
- the operator can run `clear-root` inside the mint container;
- `CLEAR_MASTER_SECRET` and `CLEAR_OPERATOR_TOKEN` are set and backed up
  according to the deployment policy;
- `CLEAR_MINT_URL` is the public URL the treasurer and wallets will use;
- root verification is current and treasury operations are explicitly enabled;
  and
- the treasurer has generated or selected a Nostr keypair out of band.

For Docker deployments, the operator-side commands are expected to run inside
the Clear container:

```bash
docker compose exec clear-operator clear-root info
docker compose exec clear-operator clear-root treasury status
```

`clear-root` is privileged. It uses the loopback operator API and should not be
treated as a remote treasurer tool.

For a new or invalidated mint, commission it before onboarding:

```bash
docker compose exec clear-operator clear-root verify
docker compose exec clear-operator clear-root treasury enable
docker compose exec clear-operator clear-root treasury status
```

## Step 1: Confirm the Current Mint State

The operator confirms that the mint is reachable and records the current CMUs:

```bash
docker compose exec clear-operator clear-root info
docker compose exec clear-operator clear-root cmu list
```

This creates a before-onboarding checkpoint for the operator's notes.

## Step 2: Collect the Treasurer npub

The treasurer provides only their public key:

```text
npub1...
```

The corresponding `nsec` stays with the treasurer and must not be sent to the
mint operator, copied into `.env`, pasted into `clear-root`, stored in the
database, or written into the deployment notes.

For development or assisted onboarding only, the helper command can generate a
keypair and print it without storing it:

```bash
docker compose exec clear-operator clear-root treasurer keygen
```

If the operator uses this helper for a lab, the `nsec` must be transferred to
the treasurer over a secure out-of-band channel and then removed from operator
notes. In normal separated custody, the treasurer generates and keeps their
own `nsec`.

## Step 3: Add the Treasurer Public Key

The operator records the treasurer's `npub`:

```bash
docker compose exec clear-operator clear-root treasurer add npub1...
```

Then the operator verifies that the treasurer is active:

```bash
docker compose exec clear-operator clear-root treasurer list
```

The add step does not create a CMU and does not issue Mint Notes. It only makes
the public key eligible for a bounded grant.

## Step 4: Create One CMU Creation Grant

The operator creates a single-use grant for that treasurer:

```bash
docker compose exec clear-operator clear-root treasurer grant npub1...
```

The command returns a grant identifier. The operator can inspect outstanding
and consumed grants with:

```bash
docker compose exec clear-operator clear-root treasurer grants
```

A first-release grant is intentionally narrow. It authorizes one
keyset/CMU-creation path for one active treasurer. After the treasurer consumes
that grant, the operator may issue another grant to the same active `npub`.
Clear rejects overlapping unused grants so each CMU creation path remains
explicit.

## Step 5: Give the Grant to the Treasurer

The operator sends the treasurer, out of band:

- the public mint URL, for example `https://clear.safebox.dev`; and
- the grant identifier from `clear-root treasurer grant`.

The operator does not send `CLEAR_OPERATOR_TOKEN`, `CLEAR_MASTER_SECRET`, the
mint database, or any keyset secret.

## Step 6: Treasurer Creates the CMU

The treasurer consumes the grant with the treasury CLI and their own `nsec`:

```bash
clear-treasury --mint https://clear.safebox.dev \
  --nsec nsec1... \
  cmu create <grant-id> \
  --name "Gym Guest Passes" \
  --unit-alias "passes"
```

The treasurer may also provide the private key through the environment:

```bash
export CLEAR_TREASURER_NSEC=nsec1...
clear-treasury --mint https://clear.safebox.dev \
  cmu create <grant-id> \
  --name "Gym Guest Passes" \
  --unit-alias "passes"
```

At creation time, the treasurer may choose `--name` and `--unit-alias` as
wallet-facing display hints for the CMU they are authorized to create. Wallets
must still bind balances to the mint URL, canonical `cmu-<keyset-id>` unit,
and keyset ID.

After the CMU exists, display metadata changes are operator-mediated. The
treasurer requests the change out of band, and the mint operator applies it:

```bash
docker compose exec clear-operator clear-root cmu label cmu-<keyset-id> \
  --name "Food Share Credits" \
  --unit-alias "shares"
```

The first argument may be either the canonical `cmu-<keyset-id>` unit or the
raw keyset ID. Label changes do not change the keyset, CMU, ledger, treasurer
authority, existing Mint Notes, or holder balances.

The treasury CLI derives the `npub` from the `nsec`, signs the request, and
sends the signed envelope to the mint's public treasury route. The mint checks
that:

- the signature is valid;
- the signed mint URL matches the mint receiving the request;
- the derived `npub` matches the grant's treasurer;
- the grant is pending and unexpired; and
- the nonce has not already been used.

If those checks pass, the mint generates a random keyset secret internally,
encrypts it at rest, consumes the grant, and creates the CMU.

The treasurer does not receive that keyset secret. The treasurer's `nsec`
authorizes bounded treasury actions; it is not the CMU signing secret. The mint
operator is responsible for safeguarding the encrypted secret, the
key-encryption material, database backups, and any host or container runtime
that can decrypt and use the signing material.

## Step 7: Treasurer Confirms Their CMU

The treasurer can ask the mint which active CMU is bound to their `nsec`:

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

This command signs a read-only `cmu:info` request. The mint returns the
requested active CMU only if that treasurer key controls the named unit, and
fails closed if the key is unknown, rotated out, inactive, or not authorized for
that CMU. `--keyset-id <keyset-id>` is also accepted when the treasurer wants to
name the underlying keyset directly.

The treasurer can inspect total supply for that CMU with:

```bash
clear-treasury --mint https://clear.safebox.dev \
  --nsec nsec1... \
  cmu summary \
  --cmu-id <cmu-id>
```

This is different from `wallet balance`: `cmu summary` reports mint-side issued,
retired, circulating, and outstanding totals for the whole CMU; `wallet balance`
reports only proofs held in the treasurer's local wallet file.

## Step 8: Operator Verifies the Result

The operator verifies that the grant was consumed and the new CMU exists:

```bash
docker compose exec clear-operator clear-root treasurer grants
docker compose exec clear-operator clear-root cmu list
```

The new CMU should also appear through public key discovery:

```bash
curl https://clear.safebox.dev/v1/keysets
curl https://clear.safebox.dev/v1/keys
```

The operator should record:

- the treasurer `npub`;
- the grant identifier;
- the CMU name;
- the resulting `cmu-<keyset-id>` unit;
- the resulting keyset ID; and
- the onboarding date and out-of-band authorization reference.

## Operator-Only Fallback

For local bootstrap, development, or tightly controlled recovery work, the
operator can consume a pending grant from inside the mint container:

```bash
docker compose exec clear-operator clear-root cmu create <grant-id> \
  --name "Gym Guest Passes" \
  --unit-alias "passes"
```

This is not the normal separated-custody treasurer flow because the treasurer
does not prove possession of the `nsec` at the moment of CMU creation. Prefer
the `clear-treasury` signed flow whenever the treasurer and operator are meant
to be operationally separate.

## Expected Failure Checks

The following failures are expected and should be treated as safety features:

- adding an `nsec` instead of an `npub` is rejected;
- consuming a grant with the wrong treasurer key is rejected;
- consuming the same grant twice is rejected;
- signing for a different mint URL is rejected;
- creating another grant for the same active treasurer while an unused grant is
  still pending is rejected; and
- `clear-root` refuses to use a non-loopback operator API URL.

## After Onboarding

After onboarding, the treasurer can issue Mint Notes for their CMU:

```bash
clear-treasury --mint https://clear.safebox.dev \
  --nsec nsec1... \
  issue 25 \
  --cmu-id <cmu-id> \
  --memo "Workshop credits"
```

By default, issued proofs are stored in a local treasurer wallet. The default
wallet path is derived from the mint URL and the treasurer `npub`:

```text
~/.clear/treasury-wallets/<mint-host>-<mint-hash>/<treasurer-npub>.json
```

This keeps different treasurer keys and different mints in separate local
wallet files. The path can be overridden with `--wallet` or
`CLEAR_TREASURY_WALLET`.

The treasurer can inspect the local wallet balance with:

```bash
clear-treasury --mint https://clear.safebox.dev \
  --nsec nsec1... \
  wallet balance
```

Or issue directly to a token instead of storing the proofs:

```bash
clear-treasury --mint https://clear.safebox.dev \
  --nsec nsec1... \
  issue 25 \
  --cmu-id <cmu-id> \
  --memo "Workshop credits" \
  --to-token
```

The treasurer can send an exact amount from the local treasury wallet to a
compatible NIP-05 address or `npub`:

```bash
clear-treasury --mint https://clear.safebox.dev \
  --nsec nsec1... \
  send 10 alice@example.com \
  --cmu-id <cmu-id> \
  --memo "Guest pass"
```

By default, the mint supplied to `clear-treasury send` must be a public HTTPS
route. The command rejects an internal-only mint URL before recipient discovery
or proof export. An operator who knows the recipient shares that mint may use
`--allow-internal-mint-delivery` together with an explicit `--relay`; omitting
either leaves the guard in place. Transfer through a Safebox operating inside
the Mainstay context remains preferable because Safebox can verify local
recipient registration.

If the wallet cannot export the exact amount but can cover it with a larger
proof, `send` refreshes the selected proof through `/v1/swap`, delivers the
requested amount, and keeps the change in the same treasurer wallet.

Delivery uses an ephemeral Nostr sender key by default. The treasurer `nsec`
authorizes treasury actions and selects the local wallet; it is not reused as
the delivery sender key.

## Recipient Public Receive Routes

Treasury delivery depends on the recipient's public receive route, not on the
recipient wallet's private or current home relay. A Safebox or Acorn may move
between Mainstay contexts, local relays, standalone relays, or hosted relays
without changing its Nostr key. When that happens, operators and recipients
must keep the public receive route current.

Use this distinction when debugging delivery:

- `home_relay` is the wallet's current private state and operating context.
  It may be local-only and must not be assumed to be reachable by a remote
  Clear treasurer.
- signed inbox relays and `public_relays` are externally reachable receive
  hints. These are the routes remote senders can use for NIP-59 gift wraps.
- a NIP-05 provider, such as Safebox Web, advertises the public receive
  context. Its relay list must name relays that outside senders can actually
  reach.

On an Acorn wallet, inspect the current public route before investigating a
missing Clear transfer:

```bash
poetry run acorn set --show-public-relays
poetry run acorn inbox-relays --json
```

If the wallet has moved context, or the public relay changed, publish the new
public route from the wallet that controls the receiving key:

```bash
poetry run acorn inbox-relays wss://spurline.safebox.dev --json
poetry run acorn set --public-relays wss://spurline.safebox.dev
```

Then verify receive discovery and pending Clear transfers:

```bash
poetry run acorn receive-clear --preview --json
poetry run acorn receive-clear --relay wss://spurline.safebox.dev --preview --json
```

If the sender returned a specific event ID, target that event directly:

```bash
poetry run acorn receive-clear --event-id <event-id> --json
poetry run acorn clear accept <event-id> --json
poetry run acorn clear balances --json
```

For Safebox Web deployments, keep the NIP-05 external relay configuration in
sync with the public route used by Acorn. The advertised relays should be
public WebSocket relay URLs, not Docker service names, loopback addresses,
VPN-only addresses, or context-local home relays.

If a stale wallet has an old cursor or stale relay route, prefer a bounded
historical scan from the relevant public relay:

```bash
poetry run acorn receive-clear --relay wss://spurline.safebox.dev \
  --since <unix-timestamp> \
  --json
```

See the Acorn relay configuration, token delivery routing, and relay migration
runbooks for the deeper model. The short operator invariant is: an Acorn can
migrate contexts safely only if its public receive route is refreshable,
inspectable, and separate from private home-relay state.

Remote treasurer retirement is separate follow-on work. Until that command
exists, `clear-root` remains the privileged local operator path for retiring
presented proofs.

Treasurer key rotation for an existing CMU belongs under:

```bash
docker compose exec clear-operator clear-root cmu rotate-treasurer cmu-<keyset-id> \
  --old-npub npub1old... \
  --new-npub npub1new... \
  --reason "out-of-band rotation reference"
```

Rotation changes the authorized treasurer `npub` for future actions. It does
not change the keyset, CMU, ledger, or existing Mint Notes.
