# Treasurer Onboarding Runbook

Status: First-release operator procedure

This runbook describes the step-by-step flow for onboarding one treasurer to
one Clear Mint Unit (CMU).

The first-release rule is strict:

```text
one active treasurer npub -> one CMU
one CMU -> one active treasurer npub
```

The treasurer's `nsec` must stay with the treasurer. The mint operator stores
only the treasurer's `npub`.

## Preconditions

Before onboarding a treasurer:

- the Clear mint is running;
- the operator can run `clear-root` inside the mint container;
- `CLEAR_MASTER_SECRET` and `CLEAR_OPERATOR_TOKEN` are set and backed up
  according to the deployment policy;
- `CLEAR_MINT_URL` is the public URL the treasurer and wallets will use; and
- the treasurer has generated or selected a Nostr keypair out of band.

For Docker deployments, the operator-side commands are expected to run inside
the Clear container:

```bash
docker compose exec clear clear-root info
```

`clear-root` is privileged. It uses the loopback operator API and should not be
treated as a remote treasurer tool.

## Step 1: Confirm the Current Mint State

The operator confirms that the mint is reachable and records the current CMUs:

```bash
docker compose exec clear clear-root info
docker compose exec clear clear-root cmu list
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
docker compose exec clear clear-root treasurer keygen
```

If the operator uses this helper for a lab, the `nsec` must be transferred to
the treasurer over a secure out-of-band channel and then removed from operator
notes. In normal separated custody, the treasurer generates and keeps their
own `nsec`.

## Step 3: Add the Treasurer Public Key

The operator records the treasurer's `npub`:

```bash
docker compose exec clear clear-root treasurer add npub1...
```

Then the operator verifies that the treasurer is active:

```bash
docker compose exec clear clear-root treasurer list
```

The add step does not create a CMU and does not issue Mint Notes. It only makes
the public key eligible for a bounded grant.

## Step 4: Create One CMU Creation Grant

The operator creates a single-use grant for that treasurer:

```bash
docker compose exec clear clear-root treasurer grant npub1...
```

The command returns a grant identifier. The operator can inspect outstanding
and consumed grants with:

```bash
docker compose exec clear clear-root treasurer grants
```

A first-release grant is intentionally narrow. It authorizes one
keyset/CMU-creation path for one active treasurer. If that treasurer has
already produced a keyset, a later `grant` for the same active `npub` must
fail.

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
  --name "Gym Guest Passes"
```

The treasurer may also provide the private key through the environment:

```bash
export CLEAR_TREASURER_NSEC=nsec1...
clear-treasury --mint https://clear.safebox.dev \
  cmu create <grant-id> \
  --name "Gym Guest Passes"
```

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

## Step 7: Treasurer Confirms Their CMU

The treasurer can ask the mint which active CMU is bound to their `nsec`:

```bash
clear-treasury --mint https://clear.safebox.dev \
  --nsec nsec1... \
  cmu info
```

Or, with `CLEAR_TREASURER_NSEC` already exported:

```bash
clear-treasury --mint https://clear.safebox.dev cmu info
```

This command signs a read-only `cmu:info` request. The mint returns the single
active CMU controlled by that treasurer key and fails closed if the key is
unknown, rotated out, inactive, or ambiguously associated with more than one
active CMU.

## Step 8: Operator Verifies the Result

The operator verifies that the grant was consumed and the new CMU exists:

```bash
docker compose exec clear clear-root treasurer grants
docker compose exec clear clear-root cmu list
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
docker compose exec clear clear-root cmu create <grant-id> \
  --name "Gym Guest Passes"
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
- creating a second grant for the same active treasurer after keyset creation
  is rejected; and
- `clear-root` refuses to use a non-loopback operator API URL.

## After Onboarding

After this first slice, the mint can advertise the new CMU and bind it to the
authorized treasurer record. Remote treasurer issuance and retirement commands
are separate follow-on work. Until those commands exist, `clear-root` remains
the privileged local operator path for existing issue, wallet, send, retire,
summary, and inspection operations.

Treasurer key rotation for an existing CMU belongs under:

```bash
docker compose exec clear clear-root cmu rotate-treasurer cmu-<keyset-id> \
  --old-npub npub1old... \
  --new-npub npub1new... \
  --reason "out-of-band rotation reference"
```

Rotation changes the authorized treasurer `npub` for future actions. It does
not change the keyset, CMU, ledger, or existing Mint Notes.
