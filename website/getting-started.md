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
```

The master secret deterministically derives denomination keys and must remain
local to the mint. The operator token protects routine issuance and retirement
actions and should be managed separately.

## Start Clear

```bash
poetry run clear \
  --host 127.0.0.1 \
  --port 3338 \
  --database ./data/clear.sqlite3 \
  --currency-name "Example Points"
```

Useful development paths:

- `http://127.0.0.1:3338/`
- `http://127.0.0.1:3338/health`
- `http://127.0.0.1:3338/docs`
- `http://127.0.0.1:3338/v1/info`
- `http://127.0.0.1:3338/v1/keys`

## Run checks

```bash
poetry run pytest
poetry run ruff check .
poetry run mkdocs build --strict
```

Clear reports the generated protocol unit and keyset identifiers at `/` and
`/v1/keys`. Record them with the organization's issuance policy before issuing
proofs.

!!! warning
    The generated unit is bound to the master secret and denomination set.
    Changing either creates a different currency. Clear refuses to open an
    existing database when the configured keyset identity does not match.
