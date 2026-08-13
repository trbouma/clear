# Clear

Clear is an experimental Cashu mint for organization-defined points. It keeps
Cashu's blinded proofs, transfer, swap, and double-spend protection while
replacing Lightning settlement with explicit treasurer-authorized issuance and
retirement.

Each Clear keyset is its own currency. Clear derives a keyset fingerprint from
the denomination public keys and binds the protocol unit to it, for example
`pts.00a1b2c3d4e5f6`. Wallets and applications must never add balances from
different units or keysets together. A friendly name is presentation metadata,
not currency identity.

## Current milestone

- Cashu-compatible key discovery, swap, and proof-state endpoints
- `clear` mint quotes authorized by an operator rather than a paid invoice
- operator-authorized proof retirement
- atomic SQLite issuance, swap, retirement, and spent-proof accounting
- FastAPI service, Poetry entry point, tests, and MkDocs documentation

Clear is developer-stage software. It has not been security reviewed and must
not be used for financial value or critical organizational accounting.

## Run locally

```bash
poetry install --with dev,docs
export CLEAR_MASTER_SECRET="$(openssl rand -hex 32)"
export CLEAR_OPERATOR_TOKEN="$(openssl rand -hex 32)"
poetry run clear --host 127.0.0.1 --port 3338 \
  --database ./data/clear.sqlite3 \
  --currency-name "Example Points"
```

Then open [http://127.0.0.1:3338/](http://127.0.0.1:3338/),
`/health`, or `/docs`.

Read the full documentation with:

```bash
poetry run mkdocs serve
```

The proposed multi-currency and signed-treasurer architecture is described in
[Multi-Currency Treasurer Authorization](docs/MULTI-CURRENCY-TREASURER-AUTHORIZATION-DESIGN.md).

## Relationship to Cashu

Clear follows the Cashu protocol's standard cryptographic and circulation
model. Its `clear` issuance and retirement method is experimental and is not a
published Cashu NUT. Standard wallets may require explicit support for custom
units and this settlement method.

- [Cashu protocol specifications](https://github.com/cashubtc/nuts)
- [Nutshell reference implementation](https://github.com/cashubtc/nutshell)

## License

MIT
