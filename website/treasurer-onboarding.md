# Onboarding a Treasurer

This page gives the first-release operator flow for adding one treasurer and
creating one treasurer-authorized Clear Mint Unit (CMU).

The rule is strict:

```text
one active treasurer npub -> one CMU
one CMU -> one active treasurer npub
```

The treasurer gives the mint operator an `npub`. The matching `nsec` stays with
the treasurer.

## 1. Confirm the Mint

Run privileged operator commands inside the Clear container:

```bash
docker compose exec clear clear-root info
docker compose exec clear clear-root cmu list
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
docker compose exec clear clear-root treasurer keygen
```

In separated custody, the treasurer should generate and keep their own `nsec`.

## 3. Add the Treasurer

```bash
docker compose exec clear clear-root treasurer add npub1...
docker compose exec clear clear-root treasurer list
```

Adding the treasurer records a public key. It does not create a CMU or issue
Mint Notes.

## 4. Grant One CMU Creation

```bash
docker compose exec clear clear-root treasurer grant npub1...
docker compose exec clear clear-root treasurer grants
```

Copy the returned grant ID. A first-release grant is single-use and intended to
produce one keyset and one CMU.

## 5. Send the Grant Out of Band

Give the treasurer:

- the mint URL, for example `https://clear.safebox.dev`; and
- the grant ID.

Do not give the treasurer `CLEAR_OPERATOR_TOKEN`, `CLEAR_MASTER_SECRET`, the
mint database, or keyset secrets.

## 6. Treasurer Creates the CMU

The treasurer consumes the grant with their `nsec`:

```bash
clear-treasury --mint https://clear.safebox.dev \
  --nsec nsec1... \
  cmu create <grant-id> \
  --name "Gym Guest Passes"
```

Or with the key in the environment:

```bash
export CLEAR_TREASURER_NSEC=nsec1...
clear-treasury --mint https://clear.safebox.dev \
  cmu create <grant-id> \
  --name "Gym Guest Passes"
```

The CLI signs the request. The mint verifies the treasurer key, mint URL,
grant, and replay nonce before generating and encrypting the new keyset secret.

## 7. Treasurer Confirms the CMU

The treasurer can ask the mint which active CMU is bound to their key:

```bash
clear-treasury --mint https://clear.safebox.dev \
  --nsec nsec1... \
  cmu info
```

Or, with `CLEAR_TREASURER_NSEC` already exported:

```bash
clear-treasury --mint https://clear.safebox.dev cmu info
```

This is a signed read-only request. The mint returns one active CMU or fails
closed.

## 8. Operator Verifies the CMU

The operator checks the consumed grant and the created CMU:

```bash
docker compose exec clear clear-root treasurer grants
docker compose exec clear clear-root cmu list
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
docker compose exec clear clear-root cmu create <grant-id> \
  --name "Gym Guest Passes"
```

Prefer the `clear-treasury` flow when the operator and treasurer are meant to
be separate. The signed flow proves that the treasurer controls the `nsec`.

## Safety Checks

These failures are expected:

- adding an `nsec` instead of an `npub` is rejected;
- consuming a grant with the wrong key is rejected;
- consuming a grant twice is rejected;
- signing for a different mint URL is rejected;
- creating another grant for the same active treasurer after CMU creation is
  rejected; and
- `clear-root` refuses non-loopback operator API URLs.

## 9. Treasurer Issues Mint Notes

After onboarding, the treasurer can issue Mint Notes for their CMU:

```bash
clear-treasury --mint https://clear.safebox.dev \
  --nsec nsec1... \
  issue 25 \
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
  --memo "Workshop credits" \
  --to-token
```

The treasurer can send an exact amount from the local wallet to a compatible
NIP-05 address or `npub`:

```bash
clear-treasury --mint https://clear.safebox.dev \
  --nsec nsec1... \
  send 10 alice@example.com \
  --memo "Guest pass"
```

If exact proofs are not available, `send` refreshes a larger proof through
`/v1/swap`, delivers the requested amount, and stores the change back in the
same treasurer wallet.

Delivery uses an ephemeral Nostr sender key by default. The treasurer `nsec`
authorizes treasury actions and selects the local wallet; it is not reused as
the delivery sender key.

Remote treasurer retirement is follow-on work.
