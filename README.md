# Clear

**Clear means Credit-Liability Ecash: Authorized and Redeemable.** It is an
experimental Cashu mint for organization-defined Mint Notes. Clear keeps
Cashu's blinded issuance, transfer, swap, and double-spend protection while
replacing Lightning settlement with explicit treasurer-authorized issuance,
redemption, and retirement.

The name describes the complete relationship: a holder receives a credit, the
issuer recognizes a corresponding liability, ecash makes that value privately
transferable, issuance is authorized, and the resulting Mint Notes are
redeemable according to the issuer's published policy. Redeemable does not
necessarily mean convertible to money, bitcoin, or another CMU.

**Clear provides the issuance, circulation and redemption machinery.** The
organization defines what each transferable unit represents and the policy
under which it is issued, accepted, redeemed, or retired.

Clear can support multiple treasurers on one mint deployment by giving each
authorized treasurer their own CMU. This lets a mint operator serve many
communities, programs, venues, or working groups from shared mint
infrastructure while keeping each community's unit, policy, ledger, and
treasurer authority separate. In the first release, that separation is
deliberately simple: one active treasurer `npub` maps to one CMU, and the
treasurer's `nsec` never enters the mint. This creates a practical new pattern
for community-issued value: one operator can provide reliable mint operations,
while many communities retain their own issuance authority.

Clear is designed to work alongside Bitcoin- and Lightning-backed Cashu mints,
not replace them. A wallet can present sat-denominated funds from those mints as
one **Cash Balance**: general-purpose value that can be transferred broadly and
settled through the Bitcoin and Lightning networks. It can present
organization-defined credits as separate **Clear Balances**. These balances
hold **transferable units**: fungible units that can move between holders under
an issuer's policy. Each Clear balance has its own issuer and policy and is
typically intended for specified products, in-kind services, allowances, or
other limited-purpose uses rather than as a cash equivalent.

**Transferable unit** is the general product category. Each Clear keyset defines
a specific **Clear Mint Unit (CMU)** as Clear's implementation of that category.
The canonical target unit is bound to the exact NUT-02 keyset ID, for example
`cmu-00a1b2c3d4e5f6`. Wallets and applications must never add balances from
different logical mints or CMUs together. One logical mint may expose an
operator-approved **mint cluster** only when its instances synchronously
coordinate authoritative issuance and spent-note state. A friendly name is
presentation metadata, not the identity of a Clear Mint Unit. When configured,
the root authority npub is part of keyset derivation, so a new root authority
creates a new CMU.

Mint Note and CMU are the canonical documentation terms. *Cashu proof* remains
the implementation term for the structure encoding a spendable note. The
running service exposes canonical `cmu-<keyset-id>` units across its API,
tokens, database identity, and tests. See
[Mint Notes Vocabulary](docs/MINT-NOTES-VOCABULARY.md).

## Current milestone

- Cashu-compatible key discovery, swap, and proof-state endpoints
- `clear` mint quotes authorized by an operator rather than a paid invoice
- operator-authorized Mint Note redemption and proof retirement
- atomic SQLite issuance, swap, retirement, and spent-proof accounting
- privileged `clear-root` bootstrap, treasury issuance, exact export, send,
  and retirement
- canonical keyset-bound CMUs with wallet-facing aliases
- NIP-05 discovery and private NIP-59 kind `7379` delivery
- signed service commissioning requests, operator attestations, and descriptors
- pending Clear transfer interoperability with Acorn and Safebox Web
- FastAPI service, Poetry entry point, tests, and MkDocs documentation

Clear is developer-stage software. It has not been security reviewed and must
not be used for financial value or critical organizational accounting.

## Run locally

```bash
poetry install --with dev,docs
export CLEAR_MASTER_SECRET="$(openssl rand -hex 32)"
export CLEAR_OPERATOR_TOKEN="$(openssl rand -hex 32)"
export CLEAR_MINT_SERVICE_NSEC="$(openssl rand -hex 32)"
export CLEAR_ROOT_AUTHORITY_NPUB="npub..."
poetry run clear --host 127.0.0.1 --port 3339 \
  --database ./data/clear.sqlite3 \
  --currency-name "Example Credits"
```

Then open [http://127.0.0.1:3339/](http://127.0.0.1:3339/),
`/health`, or `/docs`.

Read the full documentation with:

```bash
poetry run mkdocs serve
```

## Run with Docker

Create `.env` from `.env.example`, then set `CLEAR_MASTER_SECRET`,
`CLEAR_OPERATOR_TOKEN`, and `CLEAR_MINT_SERVICE_NSEC` to independently
generated secrets. `CLEAR_MINT_SERVICE_NSEC` may contain an `nsec` or a
32-byte hex private key. It supplies the mint's stable Nostr communication
identity and does not change the currency root, Cashu keysets, or treasurer
authority. `CLEAR_MINT_URL` must be the URL that wallets will use to reach the
mint; the loopback default is suitable only for local testing.

Compose publishes port `3339` on all host interfaces by default through
`CLEAR_BIND_ADDRESS=0.0.0.0`, allowing access over LAN or Tailscale. Use host
firewall rules or a more specific bind address when access must be restricted.

Inside Docker, `clear-root` connects directly to
`CLEAR_ROOT_API_URL=http://127.0.0.1:3339`. The command rejects non-loopback
API URLs. The mint separately advertises
`CLEAR_MINT_URL`, and that public URL is encoded into issued and swapped tokens.
This keeps privileged root traffic on the container loopback interface without
leaking an internal address into a circulating token.

```bash
cp .env.example .env
# Set all three secrets in .env using independent `openssl rand -hex 32` values.
docker compose up --build --detach
docker compose ps
curl http://127.0.0.1:3339/health
```

On a deployment host, pull, rebuild, recreate, and health-check Clear with:

```bash
./refresh-containers.sh
```

The mint database and privileged root wallet are stored in the named
`clear-data` volume. The same image includes `clear-root`, which can be run in
the privileged mint container with its injected operator environment:

```bash
docker compose exec clear clear-root info
docker compose exec clear clear-root issue 25 --memo "Docker lab issue"
docker compose exec clear clear-root wallet balance
docker compose exec clear clear-root summary
```

Clear reports the derived service `npub` at `/` and `/v1/info`, but never
reports its private key. It also reports the deterministic FIPS `fd00::/8`
IPv6 address derived from that `npub`; the address does not by itself indicate
that the mint is attached to or reachable through FIPS. On first configured
startup, the service `npub` is recorded beside the database. Later startup
fails if the service key is absent or derives a different `npub`. A database
created before service identities existed may adopt its first configured
identity once. The reported state is `bootstrapped` until a recognized operator
commissions the service identity. This operator relationship is separate from
any currency-root authorization of the mint's CMUs and keysets.

The service-side commissioning primitives are:

```bash
docker compose exec clear clear-root service request npub1operator...
docker compose exec -T clear clear-root service commission < attestation.json
docker compose exec clear clear-root service show
docker compose exec clear clear-root service verify
docker compose exec clear clear-root service publish \
  --relay ws://spurline:8080
```

The request is signed by the Clear service key. The attestation must be signed
by the exact requested operator and identify the same service and role. Clear
stores the complete public request, attestation, and service-signed descriptor
in its database and exposes them at `/v1/service-identity`. A Mainstay-managed
deployment wraps this exchange with `mainstay-local service commission clear`;
the Mainstay installation key never enters the Clear container.

Signed treasurer mutations start disabled. Commission the standalone mint and
then make the separate operator decision to enable them:

```bash
docker compose exec clear clear-root treasury status
docker compose exec clear clear-root verify
docker compose exec clear clear-root treasury enable
docker compose exec clear clear-root treasury status
```

`verify` creates a dedicated inactive commissioning CMU, exercises blinded
issuance, token encoding, swapping, proof-state checks, retirement, supply
reconciliation, encrypted key recovery, and audit records, and succeeds only
with zero commissioning units outstanding. It never issues against the
root/legacy CMU. Rerunning verification closes the treasury gate until the new
successful result is explicitly enabled.

Close the gate without invalidating existing Mint Notes or blocking holder
swaps:

```bash
docker compose exec clear clear-root treasury disable \
  --reason "operator maintenance"
```

`docker compose down` stops the deployment without removing the named volume.

The proposed multi-currency and signed-treasurer architecture is described in
[Multi-Currency Treasurer Authorization](docs/MULTI-CURRENCY-TREASURER-AUTHORIZATION-DESIGN.md).
The accepted first-release rule that treasurers are optional, and that one
active treasurer `npub` maps to one CMU, is described in
[First-Release Treasurer and CMU Authority Model](docs/FIRST-RELEASE-TREASURER-CMU-AUTHORITY-MODEL.md).
The accepted custody and creation model for new keysets is described in
[Treasurer-Authorized Random Keysets](docs/TREASURER-AUTHORIZED-RANDOM-KEYSETS-DESIGN.md).
The step-by-step operator and treasurer procedure is described in
[Treasurer Onboarding Runbook](docs/TREASURER-ONBOARDING-RUNBOOK.md).
The required acceptance gate before treasurer access is described in
[Root Commissioning and Treasury Readiness](docs/ROOT-COMMISSIONING-AND-TREASURY-READINESS-DESIGN.md).
The accepted implementation boundary for the first release is described in
[First Release Scope](docs/FIRST-RELEASE-SCOPE.md).
The current SQLite schema, CMU separation rules, and keyset storage model are
described in
[Clear Mint Data Schema](docs/CLEAR-MINT-DATA-SCHEMA.md).
The recommended production operations, backup, supply-limit, monitoring, and
public-edge hardening work is described in
[Clear DevOps Recommendations](docs/CLEAR-DEVOPS-RECOMMENDATIONS.md).
The current privileged root issuance, local JSON root wallet, token retirement,
and NIP-59 delivery path are described in
[Root CMU Issuance and Delivery](docs/ROOT-CMU-ISSUANCE-AND-DELIVERY.md).
The distinction among protocol transferability, operational transfer scope,
recipient acceptance, and treasury authority is defined in
[CMU Transferability, Acceptance, and Authority](docs/CMU-TRANSFERABILITY-ACCEPTANCE-AND-AUTHORITY.md).
The complete cross-product milestone is recorded in
[Transferable Clear Mint Unit Milestone](docs/TRANSFERABLE-CMU-MILESTONE-2026-08-17.md).
The working multi-community treasurer flow is recorded in
[Treasurer-Authorized CMU Milestone](docs/TREASURER-AUTHORIZED-CMU-MILESTONE-2026-09-03.md).

## Relationship to Cashu

Clear follows the Cashu protocol's standard cryptographic and circulation
model. Its `clear` issuance and retirement method is experimental and is not a
published Cashu NUT. Standard wallets may require explicit support for
keyset-bound CMU identifiers and this settlement method.

- [Cashu protocol specifications](https://github.com/cashubtc/nuts)
- [Nutshell reference implementation](https://github.com/cashubtc/nutshell)

## License

MIT
