# Transferable Clear Mint Unit Milestone

Date: 2026-08-17

## Summary

Clear, Safebox Acorn, and Safebox Web now demonstrate the first complete
delivery path for organization-issued Clear Mint Units (CMUs).

An organization can operate a Clear mint, define a named credit program, issue
CMUs into a privileged treasury wallet, inspect issued and retired supply, and
send an exact amount to a recipient's NIP-05 address. The recipient can discover
the encrypted transfer from a Nostr relay and see it as a pending Clear
transfer in Safebox Web, separate from cash payments.

This milestone establishes a practical foundation for transferable,
organization-defined value. It is still a lab implementation. Recipient
finalization into spendable Clear proof state and onward wallet spending remain
the next major implementation stage.

## Product model

Clear works alongside Bitcoin- and Lightning-backed Cashu mints:

```text
Cash Balance
  -> sat-denominated
  -> used for payments
  -> broadly transferable through Bitcoin, Lightning, and ecash

Clear Balances
  -> denominated in exact organization-defined CMUs
  -> used for transfers of credits, allowances, benefits, or service units
  -> recognized under the issuing program's policy
  -> never summed across unrelated mints or CMUs
```

The distinction is deliberate. Clear does not claim that an issuer-defined
credit is cash, legal tender, or interchangeable with another issuer's unit.

## Demonstrated flow

```text
organization configures Clear mint
  -> master secret derives active keyset and canonical CMU
  -> operator issues CMUs
  -> issued proofs enter the local root treasury wallet
  -> clear-root selects or swaps proofs for an exact amount
  -> recipient NIP-05 record advertises Clear support
  -> sender publishes NIP-59 kind 1059 gift wrap
       containing inner kind 7379 Clear transfer
  -> Acorn unwraps and validates the transfer
  -> Acorn stores it in a separate pending Clear journal
  -> Safebox Web displays the exact mint and CMU as a Clear Balance
```

The tested deployment used a public Clear mint URL, a reverse proxy, Docker,
the public relay at `wss://relay.getsafebox.app`, and a recipient resolved
through `trbouma@acorn.safebox.dev`.

## Clear mint and treasury capabilities

The implemented Clear service provides:

- deterministic key derivation from `CLEAR_MASTER_SECRET`;
- optional root-authority participation through
  `CLEAR_ROOT_AUTHORITY_NPUB`;
- canonical keyset-bound units in the form `cmu-<keyset-id>`;
- a public mint URL distinct from the privileged loopback API URL;
- wallet-facing currency name, alias, and unit alias metadata;
- Cashu-compatible key discovery, issuance, swap, proof-state, and retirement;
- SQLite issuance, spent-proof, retirement, and audit accounting;
- operator-protected issuance and retirement endpoints;
- issued, retired, circulating, and outstanding supply summaries;
- a JSON-backed root treasury wallet;
- exact-amount export using proof selection and swap change;
- Cashu token encoding for transport;
- Docker deployment on the default Clear port `3339`; and
- NIP-05 discovery and NIP-59 Clear transfer delivery.

## Operator workflow

Inside the Clear container:

```sh
docker compose exec clear clear-root info
docker compose exec clear clear-root summary
docker compose exec clear clear-root wallet balance
docker compose exec clear clear-root wallet list
```

Issue CMUs into the local treasury wallet:

```sh
docker compose exec clear clear-root issue 100 \
  --memo "Program allocation"
```

Send an exact amount:

```sh
docker compose exec clear clear-root send 100 \
  recipient@example.org \
  --memo "Program transfer"
```

Retire returned CMUs:

```sh
docker compose exec clear clear-root retire 25 \
  --memo "Program settlement"
```

`issued` is the cumulative amount created. `retired` is the amount permanently
removed. `circulating` is issued minus retired and includes CMUs held by the
treasury and by recipient wallets. The local root wallet balance is the subset
still held by `clear-root` and available to send.

## Transfer envelope

The delivery protocol is:

```text
outer kind: 1059
inner kind: 7379
protocol: clear-token-transfer
transport: nip59
unit: cmu-<keyset-id>
```

The encrypted inner payload carries the Cashu token, exact mint URL, canonical
CMU, amount, keyset IDs, and optional memo. Sender identity is ephemeral by
default so a lab operator does not need to manage a persistent sender key.

## Wallet boundary

Acorn deliberately separates Clear transfer receipts from ordinary ecash:

- kind `7378` remains the incoming cash/ecash path;
- kind `7379` is the incoming Clear transfer path;
- cash proofs remain in kind `7375`;
- future spendable Clear proofs use kind `7380`; and
- Clear transaction history uses kind `7381`.

Safebox Web presents one singular **Cash Balance** and plural **Clear
Balances**. Clear balances are grouped by exact `(mint URL, CMU)` identity.
Friendly aliases improve display but never replace canonical identity.

## Safety and trust boundary

This milestone does not establish production readiness.

- `clear-root` is a privileged bootstrap utility, not the future treasurer product.
- The operator token is a root bootstrap boundary, not signed,
  currency-scoped treasurer authorization.
- The software has not received an independent security audit.
- Clear credits depend on the issuer's policy and ability to honour them.
- A root authority, mint operator, and treasurer may currently be the same
  person even though the product model treats them as separate roles.
- Keyset rotation creates a distinct CMU; it does not silently preserve
  currency equivalence.
- Recipient wallets can receive and dismiss pending transfers, but cannot yet
  finalize and spend them through the complete Clear wallet workflow.

Use only test units with no promise of financial value.

## Next implementation stage

The next end-to-end milestone is:

1. validate and refresh a pending kind `7379` token against its Clear mint;
2. persist resulting proofs in encrypted kind `7380` state;
3. append the balance change to kind `7381` history;
4. remove bearer material from the pending receipt;
5. expose explicit accept and reject controls;
6. spend or send from one exact Clear balance; and
7. preserve crash recovery across mint mutation and relay persistence.

After that foundation is reliable, the privileged root bootstrap authority can be
replaced with separately installable, signed, currency-scoped treasurer
authorization.
