---
title: Getting Started
description: Run a local Clear development mint.
---

# Getting Started

## Install

```bash
git clone https://github.com/trbouma/clear.git
cd clear
poetry install --with dev,docs
```

## Configure secrets

Generate independent development secrets:

```bash
export CLEAR_MASTER_SECRET="$(openssl rand -hex 32)"
export CLEAR_OPERATOR_TOKEN="$(openssl rand -hex 32)"
export CLEAR_ROOT_AUTHORITY_NPUB="npub..."
export CLEAR_MINT_URL="http://127.0.0.1:3339"
export CLEAR_CURRENCY_ALIAS="Harbour Lab Credits"
export CLEAR_CURRENCY_UNIT_ALIAS="smiles"
export CLEAR_LAB_API_URL="http://127.0.0.1:3339"
```

The master secret deterministically derives denomination keys and must remain
local to the mint. When `CLEAR_ROOT_AUTHORITY_NPUB` is configured, it is also
included in keyset derivation so a root authority change creates a new CMU.
The operator token protects routine lab issuance and retirement actions and
should be managed separately.
The optional currency alias and unit alias are wallet-facing display hints for
this CMU.

`CLEAR_MINT_URL` is the canonical URL advertised to wallets and encoded in
tokens. `CLEAR_LAB_API_URL` is the private connection used by `clear-lab`. A
Docker deployment keeps the latter on container loopback even when the former
is a public HTTPS URL behind a reverse proxy.

## Start Clear

```bash
poetry run clear \
  --host 127.0.0.1 \
  --port 3339 \
  --database ./data/clear.sqlite3 \
  --currency-name "Example Credits"
```

Useful development paths:

- `http://127.0.0.1:3339/`
- `http://127.0.0.1:3339/health`
- `http://127.0.0.1:3339/docs`
- `http://127.0.0.1:3339/v1/info`
- `http://127.0.0.1:3339/v1/keys`

## Lab CLI

```bash
poetry run clear-lab configure \
  --currency-name "Harbour Credits" \
  --currency-alias "Harbour Lab Credits" \
  --currency-unit-alias "smiles" \
  --root-authority-npub "npub..."
poetry run clear-lab info
poetry run clear-lab issue 25 --memo "wallet circulation test"
poetry run clear-lab wallet balance
poetry run clear-lab withdraw 25 --memo "disbursement"
poetry run clear-lab issue 5 --memo "immediate token" --to-token
poetry run clear-lab address alice@example.com
poetry run clear-lab send 5 alice@example.com --memo "address delivery"
poetry run clear-lab redeem "cashuA..." --memo "returned from wallet"
poetry run clear-lab summary
```

A Lightning-address or NIP-05 well-known response can advertise lab Clear
delivery with a `clear` object. The current Safebox-compatible shape
advertises NIP-59 delivery with inner kind `7379`:

```json
{
  "clear": {
    "alice": {
      "protocols": ["clear-token-transfer"],
      "transports": ["nip59"],
      "kinds": [7379],
      "mints": ["http://127.0.0.1:3339"],
      "units": ["cmu-0011223344556677"]
    }
  }
}
```

The `mints` and `units` arrays are optional restrictions. When omitted, the
receiver advertises general Clear support and validates the mint, CMU, and
keyset ids after decrypting the transfer.

## Run checks

```bash
poetry run pytest
poetry run ruff check .
poetry run mkdocs build --strict
```

Clear reports the generated protocol unit and keyset identifiers at `/` and
`/v1/keys`. Record them with the organization's issuance policy before issuing
Mint Notes.
The `/v1/info` response also includes a suggested wallet alias. Wallets may
display it, but must still bind balances to the mint URL, CMU, and keyset id.

!!! warning
    The target unit is `cmu-<keyset-id>` and is bound to the exact keyset.
    Changing the master secret, configured root authority npub, or denomination
    set creates a new keyset and a new CMU. Clear refuses to open an existing
    database when the configured keyset identity does not match.

!!! note "Current implementation vocabulary"
    Until the code migration is completed, the running prototype may report a
    prototype unit instead of `cmu-<keyset-id>`. Do not rewrite an
    existing database value by hand.
