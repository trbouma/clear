# First-Release Treasurer and CMU Authority Model

Status: Accepted first-release constraint

## Decision

Treasurers are optional. A Clear mint may continue to operate in the simple
single-operator model with no treasurers configured.

When treasurers are configured for the first release, each CMU has one active
treasurer, while a treasurer may control more than one CMU:

```text
one active treasurer npub -> one or more CMUs
one CMU -> one active treasurer npub
```

The treasurer gives the mint operator only their Nostr public key (`npub`).
The corresponding private key (`nsec`) stays with the treasurer and is never
stored in mint configuration, the Clear database, logs, backups, or API
requests.

## Single-Operator Mode

Before treasurers are enabled, the mint operator remains the treasury
authority. `clear-root` runs inside the mint container or another trusted local
mint environment and uses the loopback operator API plus `CLEAR_OPERATOR_TOKEN`
to issue, send, retire, inspect, and summarize CMU activity.

This mode remains valid for operators who do not need separated treasury
authority.

```text
mint operator
  -> clear-root issue
  -> clear-root send
  -> clear-root retire
  -> clear-root summary
```

No treasurer registry, signed treasurer authorization, grant, or remote
treasury CLI is required in this mode.

## Treasurer Establishment

Establishing a treasurer does not disclose private key material and does not
itself create spendable supply.

The intended first-release ceremony is:

```text
treasurer generates or selects nsec out of band
  -> treasurer gives corresponding npub to mint operator
  -> operator adds that npub as an authorized treasurer
  -> operator grants that treasurer one CMU
  -> treasurer signs one keyset creation request
  -> mint generates and encrypts a random keyset secret internally
  -> resulting keyset defines exactly one CMU
```

The mint stores the authorized treasurer `npub`, the consumed grant, the signed
request, and the resulting keyset/CMU binding. It never receives or derives the
treasurer `nsec`.

The operator runbook for this ceremony is
[Treasurer Onboarding Runbook](TREASURER-ONBOARDING-RUNBOOK.md).

## Authority Versus Keyset Custody

Treasurer authority and keyset custody are separate. The treasurer `nsec` signs
bounded treasury requests. It does not derive, decrypt, export, or store the CMU
keyset secret.

For treasurer-created CMUs:

```text
treasurer nsec -> authorization authority
mint-held keyset secret -> Cashu signing custody
```

The mint operator is responsible for safeguarding the keyset secret and
everything that can decrypt or use it: `CLEAR_KEY_ENCRYPTION_KEY`, encrypted
keyset-secret rows, database backups, host/container access, and runtime
signing paths. The treasurer never sees the keyset secret.

If a treasurer `nsec` is compromised, an attacker may authorize actions for
that CMU while the key remains active. If the keyset secret is compromised, an
attacker may create valid Mint Notes outside the mint ledger. That is a deeper
supply-integrity failure because software authorization checks can be bypassed.

The keyset secret is not rotated for an existing CMU. A new keyset secret
creates a new keyset and therefore a new CMU. Treasurer `npub` rotation changes
authority for future actions without changing keyset custody or CMU identity.

## Friendly Display Metadata

Friendly display metadata is not CMU identity. Wallets and applications may
show a human name such as `Food Share Credits` and a unit label such as
`shares`, but balances must still bind to:

```text
mint URL + cmu-<keyset-id> + keyset ID
```

At CMU creation time, the treasurer may set the initial wallet-facing display
metadata as part of the signed grant-consumption request:

```text
clear-treasury cmu create <grant-id> \
  --name "Food Share Credits" \
  --unit-alias "shares"
```

After the CMU exists, display metadata changes are operator-mediated. The
treasurer requests the change out of band, and the mint operator applies it
with the privileged local root CLI:

```text
clear-root cmu label cmu-<keyset-id> \
  --name "Food Share Credits" \
  --unit-alias "shares"
```

This keeps the mint operator responsible for the metadata the mint publicly
advertises, while still letting the treasurer choose the initial presentation
for the unit they are authorized to create. Changing friendly labels does not
change the keyset, CMU, ledger, treasurer authority, existing Mint Notes, or
holder balances.

## Public Listing Visibility

Public listing is a discovery and presentation control, not a lifecycle state.
An unlisted CMU is hidden from the mint home page but remains available to
software that already knows its exact CMU id or keyset ID. It remains visible
through direct keyset endpoints, can still issue, swap, redeem, retire, and be
inspected, and it keeps the same keyset, ledger, treasurer authority, existing
Mint Notes, and holder balances.

Both the mint operator and the CMU treasurer may change public listing, but
they do so through different authority paths:

- the mint operator may unilaterally list or unlist any CMU hosted by the mint
  through the privileged local `clear-root` operator surface; and
- a treasurer may list or unlist only the CMUs currently bound to their
  treasurer key through a signed `clear-treasury` request.

Operator commands:

```text
clear-root cmu unlist cmu-<keyset-id>
clear-root cmu list cmu-<keyset-id>
```

Treasurer commands:

```text
clear-treasury --mint <mint-url> --nsec <treasurer-nsec> \
  cmu unlist --cmu-id cmu-<keyset-id>

clear-treasury --mint <mint-url> --nsec <treasurer-nsec> \
  cmu list --cmu-id cmu-<keyset-id>
```

This is intentionally separate from friendly label changes. Label changes are
operator-mediated because they affect the public wording the mint advertises.
Public listing lets the operator or authorized treasurer decide whether an
otherwise active CMU should appear in public home-page discovery.

In the `clear-root` command model, `add` and `grant` have distinct meanings:

- `clear-root treasurer keygen` generates a local `npub`/`nsec` pair and
  stores nothing. It is a convenience for development or assisted onboarding;
  in normal separated custody, the treasurer should generate and keep their own
  `nsec`.
- `clear-root treasurer add <npub>` records a treasurer public key that may be
  considered for authority.
- `clear-root treasurer grant <npub>` sets up one permitted keyset/CMU
  creation path for that treasurer.
- `clear-root cmu create <grant-id> --name <name>` consumes the pending grant,
  generates the mint-held random keyset, and creates the corresponding CMU.
- `clear-root cmu list` shows the legacy/default CMU and any treasurer-created
  CMUs.

For the first release, each grant is single-use and CMU-creating in intent.
The operator may issue another grant to the same active treasurer after the
previous grant is consumed. Clear still rejects overlapping unused grants for
the same treasurer so every CMU creation path remains explicit.

## Treasury CLI Resolution

The remote treasury CLI is identity-driven. In the normal first-release path,
the treasurer supplies only:

```text
mint URL + treasurer nsec
```

The CLI derives the corresponding `npub`, resolves the intended CMU id or
keyset ID to a keyset, asks the mint which CMU is currently authorized for that
`npub` and keyset, and signs actions for that CMU.

```text
treasury CLI has nsec
  -> derives npub
  -> CLI resolves cmu-... or keyset ID to one keyset
  -> mint resolves npub and required keyset ID to one CMU
  -> CLI signs issue or retire action for that CMU
  -> mint verifies signature against the CMU's current treasurer npub
```

The CLI requires an explicit CMU selector even when the treasurer controls only
one active CMU. The recommended selector is `--cmu-id cmu-...`; `--keyset-id`
is accepted when the treasurer wants to name the underlying keyset directly.
This prevents habit-forming commands that later become ambiguous.

Required failure cases:

- no CMU is bound to the derived `npub`;
- the `npub` was rotated out;
- the signed request omits the resolved keyset ID;
- the derived `npub` does not control the requested keyset;
- the CMU is suspended or not active for the requested action; or
- the treasury gate is closed.

The first release must reject ambiguous treasury operations instead of guessing
which CMU a treasurer intended.

## Authority Rotation

Treasurer key rotation changes the authorized `npub` for an existing CMU. It
does not rotate the Cashu keyset and does not create a new CMU.

```text
same mint URL
same keyset
same cmu-<keyset-id>
same ledger
old treasurer npub -> new treasurer npub
```

The ceremony that proves or agrees to the replacement is out of band between
the mint operator and treasurer. The mint records only the resulting authority
change, including the old `npub`, new `npub`, CMU, operator/root action,
timestamp, and reason or audit reference.

The operator must supply both the current and replacement public keys:

```text
clear-root cmu rotate-treasurer cmu-<keyset-id> \
  --old-npub npub1old... \
  --new-npub npub1new... \
  --reason <text>
```

The command must fail unless `--old-npub` exactly matches the CMU's current
authority record. This makes rotation a deliberate compare-and-swap operation
and reduces the chance of rotating the wrong CMU or replacing an authority that
has already changed.

After rotation:

- the old `npub` cannot authorize new actions for the CMU;
- the new `npub` authorizes future actions for the same CMU;
- existing Mint Notes remain valid;
- wallet balances do not migrate or relabel as a new unit;
- pending unconsumed authorizations from the old `npub` become invalid; and
- historical authorizations remain audit evidence.

This is distinct from keyset rotation. Keyset rotation creates a new CMU.
Treasurer authority rotation keeps the existing CMU.

## CMU Lifecycle Commands

Whole-unit lifecycle changes must live under a `cmu` command group so they
cannot be confused with retiring presented Mint Notes.

The existing top-level command remains note/amount scoped:

```text
clear-root retire 25
clear-root retire <cashu-token>
clear-root retire --proofs-file returned-proofs.json
```

Those commands retire presented notes from circulation and change supply
accounting.

Whole-CMU lifecycle commands are scoped under `cmu`:

```text
clear-root cmu suspend cmu-<keyset-id> --reason <text>
clear-root cmu resume cmu-<keyset-id> --reason <text>
clear-root cmu redemption-only cmu-<keyset-id> --reason <text>
clear-root cmu retire cmu-<keyset-id> --reason <text>
```

`clear-root cmu retire` retires the mint unit as a lifecycle state after its
policy-defined wind-down. It does not mean that unpresented bearer Mint Notes
were individually retired. Presented notes are still retired through the
top-level `clear-root retire` command.

## External View

From a wallet or holder perspective, treasurer governance is mostly internal
mint policy. A treasurer-authorized unit appears as another CMU offered by the
same mint:

```text
mint: https://clear.example
unit: cmu-<keyset-id>
keyset_id: <keyset-id>
friendly_alias: Example Credits
```

Wallets group balances by mint URL, CMU, and keyset ID. They do not need the
treasurer's `npub` to hold or transfer Mint Notes. A treasurer `npub` rotation
therefore should not change the holder-facing balance identity.

## First-Release Invariants

- Treasurers are optional.
- `clear-root` remains the local single-operator path when no treasurers are
  configured.
- The mint stores treasurer `npub` values only, never treasurer `nsec` values.
- One active treasurer `npub` may control multiple CMUs.
- One CMU has exactly one active treasurer `npub`.
- `clear-root treasurer grant <npub>` must fail while that treasurer already
  has an unused grant.
- Treasurer operations must include a CMU id or keyset ID.
- A treasurer-created CMU is defined by its keyset, not by the treasurer key.
- Treasurer `npub` rotation changes future authority only.
- Keyset rotation creates a new CMU.
- Whole-unit lifecycle transitions belong under `clear-root cmu`.
- Top-level `clear-root retire` retires presented notes, amounts, tokens, or
  proofs.
- Existing Mint Notes survive treasurer removal or `npub` rotation.
- Ambiguous multi-CMU control by one `npub` is deferred.
- Switching mint operators by exporting a CMU's circulation state and
  importing it into another mint is deferred, but the model keeps treasurer
  authority separate from mint operation so that migration can be added later.
