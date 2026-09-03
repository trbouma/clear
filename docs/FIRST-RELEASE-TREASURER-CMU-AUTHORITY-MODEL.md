# First-Release Treasurer and CMU Authority Model

Status: Accepted first-release constraint

## Decision

Treasurers are optional. A Clear mint may continue to operate in the simple
single-operator model with no treasurers configured.

When treasurers are configured for the first release, Clear uses a strict
one-to-one authority model:

```text
one active treasurer npub -> one CMU
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

In the `clear-root` command model, `add` and `grant` have distinct meanings:

- `clear-root treasurer keygen` generates a local `npub`/`nsec` pair and
  stores nothing. It is a convenience for development or assisted onboarding;
  in normal separated custody, the treasurer should generate and keep their own
  `nsec`.
- `clear-root treasurer add <npub>` records a treasurer public key that may be
  considered for authority.
- `clear-root treasurer grant <npub>` sets up that treasurer's one permitted
  keyset/CMU creation path.
- `clear-root cmu create <grant-id> --name <name>` consumes the pending grant,
  generates the mint-held random keyset, and creates the corresponding CMU.
- `clear-root cmu list` shows the legacy/default CMU and any treasurer-created
  CMUs.

For the first release, `grant` is single-use and CMU-creating in intent. If a
grant for that treasurer has already produced a keyset, a second grant for the
same active treasurer must fail. The operator should rotate the treasurer
`npub` for the existing CMU, suspend/remove the treasurer, or use a later
explicit multi-CMU model instead of silently creating another unit.

## Treasury CLI Resolution

The remote treasury CLI is identity-driven. In the normal first-release path,
the treasurer supplies only:

```text
mint URL + treasurer nsec
```

The CLI derives the corresponding `npub`, asks the mint which CMU is currently
authorized for that `npub`, and signs actions for that CMU.

```text
treasury CLI has nsec
  -> derives npub
  -> mint resolves npub to exactly one CMU
  -> CLI signs issue or retire action for that CMU
  -> mint verifies signature against the CMU's current treasurer npub
```

The CLI should not require a normal treasurer to manually choose a keyset or
CMU. If the derived `npub` is not the current authority for exactly one CMU,
the command fails closed.

Required failure cases:

- no CMU is bound to the derived `npub`;
- the `npub` was rotated out;
- the mint returns more than one CMU for the `npub`;
- the CMU is suspended or not active for the requested action; or
- the treasury gate is closed.

The first release must reject the ambiguous "one `npub` controls multiple
CMUs" case instead of adding selection UX.

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
- One active treasurer `npub` resolves to exactly one CMU.
- One CMU has exactly one active treasurer `npub`.
- `clear-root treasurer grant <npub>` must fail if that treasurer has already
  created a keyset/CMU.
- A treasurer-created CMU is defined by its keyset, not by the treasurer key.
- Treasurer `npub` rotation changes future authority only.
- Keyset rotation creates a new CMU.
- Whole-unit lifecycle transitions belong under `clear-root cmu`.
- Top-level `clear-root retire` retires presented notes, amounts, tokens, or
  proofs.
- Existing Mint Notes survive treasurer removal or `npub` rotation.
- Ambiguous multi-CMU control by one `npub` is deferred.
