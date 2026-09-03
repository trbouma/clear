# Treasurer-Authorized CMU Milestone

Date: 2026-09-03

## Summary

Clear now demonstrates a working treasurer-authorized CMU flow on a running
public mint.

A mint operator can authorize a treasurer by `npub`, grant that treasurer one
CMU creation path, and let the treasurer consume the grant remotely with their
own `nsec`. The mint receives only signed Nostr authorization envelopes and
never receives the treasurer private key. The resulting CMU has its own keyset,
canonical `cmu-<keyset-id>` unit, friendly display metadata, local treasurer
wallet, and treasurer-authorized issuance path.

The flow has been tested end to end with Clear and Safebox Web: a treasurer
created a CMU, set wallet-facing labels, issued Mint Notes into a
treasurer-scoped wallet, sent them through NIP-59 delivery, and confirmed that
Safebox Web received and displayed the friendly CMU name and unit alias.

## Product Significance

This milestone shows the multi-community mint model in practice.

One Clear operator can run shared mint infrastructure while many separate
communities, programs, venues, or working groups each receive their own
treasurer-authorized CMU. Each community can have:

- its own active treasurer `npub`;
- its own random encrypted keyset;
- its own canonical CMU identity;
- its own friendly name and unit alias;
- its own local treasurer wallet; and
- its own issuance and delivery workflow.

The first-release rule remains intentionally strict:

```text
one active treasurer npub -> one CMU
one CMU -> one active treasurer npub
```

This keeps the authority model simple while proving that one operator can
support many communities without merging their ledgers, balances, or issuance
authority.

## Demonstrated Flow

```text
treasurer generates or selects nsec
  -> treasurer gives npub to mint operator
  -> operator adds treasurer npub
  -> operator creates a single-use CMU creation grant
  -> treasurer consumes grant with clear-treasury cmu create
  -> mint verifies signed Stroma/Nostr envelope
  -> mint generates and encrypts a random keyset secret
  -> mint advertises the new CMU through keyset discovery
  -> treasurer confirms authority with clear-treasury cmu info
  -> treasurer issues Mint Notes with clear-treasury issue
  -> issued proofs enter a treasurer-scoped local wallet
  -> treasurer sends exact amount with clear-treasury send
  -> Clear/Safebox NIP-59 delivery reaches Safebox Web
  -> Safebox Web displays friendly CMU labels from mint keyset metadata
```

The tested display metadata used:

```text
friendly_alias: Food Share Credits
friendly_unit_alias: shares
```

Safebox Web displays the friendly labels while preserving the canonical balance
identity underneath.

## Implemented Clear Capabilities

The Clear mint now provides:

- persistent treasurer authority records;
- single-use treasurer CMU creation grants;
- Stroma-backed signed treasury envelopes;
- public signed treasury endpoints for CMU creation, CMU info, and quote
  authorization;
- random keyset generation for treasurer-created CMUs;
- encrypted-at-rest random keyset secrets;
- multi-keyset discovery through `/v1/keysets`, `/v1/keys`, and
  `/v1/keys/{keyset_id}`;
- CMU display metadata including `friendly_alias` and
  `friendly_unit_alias`;
- operator-mediated label updates through `clear-root cmu label`;
- treasurer-scoped local wallet paths derived from mint URL and treasurer
  `npub`;
- treasurer issuance through `clear-treasury issue`; and
- treasurer delivery through `clear-treasury send`.

## Command Surface

Operator-side commands run inside the mint container:

```bash
docker compose exec clear clear-root treasurer add <npub>
docker compose exec clear clear-root treasurer grant <npub>
docker compose exec clear clear-root treasurer grants
docker compose exec clear clear-root cmu list
docker compose exec clear clear-root cmu label cmu-<keyset-id> \
  --name "Food Share Credits" \
  --unit-alias "shares"
```

Treasurer-side commands run outside the mint with the treasurer's `nsec`:

```bash
clear-treasury --mint https://clear.safebox.dev \
  --nsec nsec1... \
  cmu create <grant-id> \
  --name "Food Share Credits" \
  --unit-alias "shares"

clear-treasury --mint https://clear.safebox.dev \
  --nsec nsec1... \
  cmu info

clear-treasury --mint https://clear.safebox.dev \
  --nsec nsec1... \
  issue 25 \
  --memo "Food share allocation"

clear-treasury --mint https://clear.safebox.dev \
  --nsec nsec1... \
  wallet balance

clear-treasury --mint https://clear.safebox.dev \
  --nsec nsec1... \
  send 10 recipient@example.org \
  --memo "Food share"
```

## Display Metadata Policy

Friendly display metadata is presentation only. Wallets and applications may
show a human name and unit label, but balances must still bind to:

```text
mint URL + cmu-<keyset-id> + keyset ID
```

The treasurer may choose the initial friendly name and unit alias when
consuming the CMU creation grant. After the CMU exists, label changes are
operator-mediated:

```bash
docker compose exec clear clear-root cmu label cmu-<keyset-id> \
  --name "Food Share Credits" \
  --unit-alias "shares"
```

Changing friendly labels does not change the keyset, CMU, ledger, treasurer
authority, existing Mint Notes, or holder balances.

## Wallet Boundary

The treasurer wallet is local bearer state. By default, wallet files are scoped
by mint URL and treasurer `npub`:

```text
~/.clear/treasury-wallets/<mint-host>-<mint-hash>/<treasurer-npub>.json
```

Different treasurer `nsec` values and different mints therefore use different
wallet files. The path can be overridden with `--wallet` or
`CLEAR_TREASURY_WALLET`.

Wallet encryption is deferred. Until then, treasurer wallet files must be
treated as hot bearer wallets and protected by local OS controls.

## Safety and Trust Boundary

This remains developer-stage software.

- The treasurer `nsec` stays outside the mint.
- The mint stores authorized treasurer `npub` values only.
- Treasurer-created keysets use mint-held random secrets encrypted at rest.
- Friendly labels are display hints, not currency identity.
- `clear-root` remains a privileged local operator tool.
- Remote treasurer retirement is not implemented yet.
- Treasurer rotation is documented but not yet implemented.
- The software has not received an independent security audit.

Use only test units with no promise of financial value.

## Next Implementation Stage

The next natural slices are:

1. implement `clear-treasury retire`;
2. implement `clear-root cmu rotate-treasurer` with old-`npub` compare-and-swap;
3. add stricter local wallet file permissions;
4. add encrypted treasury wallet support; and
5. add richer treasurer activity/history views.
