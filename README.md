# Clear

Clear is an experimental Cashu mint for organization-defined Mint Notes. It
keeps Cashu's blinded issuance, transfer, swap, and double-spend protection
while replacing Lightning settlement with explicit treasurer-authorized
issuance, redemption, and retirement.

Clear is designed to work alongside Bitcoin- and Lightning-backed Cashu mints,
not replace them. A wallet can present sat-denominated funds from those mints as
one **Cash Balance**: general-purpose value that can be transferred broadly and
settled through the Bitcoin and Lightning networks. It can present
organization-defined credits as separate **Clear Balances**. Each Clear balance
has its own issuer and policy and is typically intended for specified products,
in-kind services, allowances, or other limited-purpose uses rather than as a
cash equivalent.

Each Clear keyset defines its own Clear Mint Unit (CMU). The canonical target unit is
bound to the exact NUT-02 keyset ID, for example
`cmu-00a1b2c3d4e5f6`. Wallets and applications must never add balances from
different logical mints or CMUs together. One logical mint may expose an
operator-approved **mint cluster** only when its instances synchronously
coordinate authoritative issuance and spent-note state. A friendly name is
presentation metadata, not the identity of a Clear Mint Unit. When configured,
the root authority npub is part of keyset derivation, so a new root authority
creates a new CMU.

Mint Note and CMU are the canonical documentation terms. *Cashu proof* remains
the implementation term for the structure encoding a spendable note. The
current code may still expose older prototype unit identifiers until the code,
API, database, and test migration is completed. See
[Mint Notes Vocabulary](docs/MINT-NOTES-VOCABULARY.md).

## Current milestone

- Cashu-compatible key discovery, swap, and proof-state endpoints
- `clear` mint quotes authorized by an operator rather than a paid invoice
- operator-authorized Mint Note redemption and proof retirement
- atomic SQLite issuance, swap, retirement, and spent-proof accounting
- FastAPI service, Poetry entry point, tests, and MkDocs documentation

Clear is developer-stage software. It has not been security reviewed and must
not be used for financial value or critical organizational accounting.

## Run locally

```bash
poetry install --with dev,docs
export CLEAR_MASTER_SECRET="$(openssl rand -hex 32)"
export CLEAR_OPERATOR_TOKEN="$(openssl rand -hex 32)"
export CLEAR_ROOT_AUTHORITY_NPUB="npub..."
poetry run clear --host 127.0.0.1 --port 3338 \
  --database ./data/clear.sqlite3 \
  --currency-name "Example Credits"
```

Then open [http://127.0.0.1:3338/](http://127.0.0.1:3338/),
`/health`, or `/docs`.

Read the full documentation with:

```bash
poetry run mkdocs serve
```

## Run with Docker

Create `.env` from `.env.example`, then set `CLEAR_MASTER_SECRET` and
`CLEAR_OPERATOR_TOKEN` to independently generated secrets. `CLEAR_MINT_URL`
must be the URL that wallets will use to reach the mint; the loopback default
is suitable only for local testing.

```bash
cp .env.example .env
# Set both required secrets in .env using independent `openssl rand -hex 32` values.
docker compose up --build --detach
docker compose ps
curl http://127.0.0.1:3338/health
```

The mint database and the privileged lab wallet are stored in the named
`clear-data` volume. The same image includes `clear-lab`, which can be run in
the privileged mint container with its injected operator environment:

```bash
docker compose exec clear clear-lab info
docker compose exec clear clear-lab issue 25 --memo "Docker lab issue"
docker compose exec clear clear-lab wallet balance
docker compose exec clear clear-lab summary
```

`docker compose down` stops the deployment without removing the named volume.

The proposed multi-currency and signed-treasurer architecture is described in
[Multi-Currency Treasurer Authorization](docs/MULTI-CURRENCY-TREASURER-AUTHORIZATION-DESIGN.md).
The accepted implementation boundary for the first release is described in
[First Release Scope](docs/FIRST-RELEASE-SCOPE.md).
The current privileged lab issuance, local JSON lab wallet, token retirement,
and NIP-59 delivery path are described in
[Lab CMU Issuance and Delivery](docs/LAB-CMU-ISSUANCE-AND-DELIVERY.md).

## Relationship to Cashu

Clear follows the Cashu protocol's standard cryptographic and circulation
model. Its `clear` issuance and retirement method is experimental and is not a
published Cashu NUT. Standard wallets may require explicit support for
keyset-bound CMU identifiers and this settlement method.

- [Cashu protocol specifications](https://github.com/cashubtc/nuts)
- [Nutshell reference implementation](https://github.com/cashubtc/nutshell)

## License

MIT
