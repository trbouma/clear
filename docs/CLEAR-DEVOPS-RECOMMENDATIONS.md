# Clear DevOps Recommendations

Status: Recommended production-hardening direction  
Date: 2026-09-07

## Purpose

This note translates the operational lessons in
[Running a Cashu mint - best practices](https://gist.github.com/callebtc/ec4d41582e356b63989f7a9a57bba831)
into Clear's trust and settlement model. It also accounts for the current
[NUT-02 keyset and fee model](https://github.com/cashubtc/nuts/blob/main/02.md)
and [NUT-06 mint information model](https://github.com/cashubtc/nuts/blob/main/06.md).

The source guidance is primarily written for a Lightning-backed Cashu mint.
Clear is different: it issues organization-defined transferable units through
explicit operator or treasurer authorization and does not promise conversion
to Lightning. The same bearer-ecash risks still apply, but reserve management
must be translated into issuer authorization, outstanding-liability limits,
and the issuer's documented ability to honor the unit.

This is a recommendation document. Unless identified as a current safeguard,
the controls below are not yet implemented and must not be inferred from a
healthy `/health` response.

## Executive Recommendation

Before Clear is used for non-disposable value, prioritize five controls:

1. enforce transaction and outstanding-supply ceilings independently for each
   CMU;
2. provide a live-safe backup, restore, and integrity-verification workflow;
3. protect public protocol endpoints with bounded requests, rate limits,
   pending-quote expiry, and trusted-proxy handling;
4. publish useful NUT-06 operator, route, limit, and notice metadata; and
5. monitor supply reconciliation, database growth, disk capacity, backup age,
   treasury state, and service identity continuously.

Keyset rotation and spent-proof pruning should follow only after Clear defines
an explicit lifecycle compatible with keyset-bound CMU identity. They should
not be copied mechanically from a sat-denominated mint.

## Clear Risk Model

### Bearer value and spent-proof durability

Mint Notes live in holder wallets. Clear stores the spent-proof nullifiers that
prevent those notes from being spent twice. Losing holder-independent mint
state therefore does not merely lose an account database: it can cause Clear
to forget prior spends and accept the same note again.

The authoritative recovery unit includes more than `clear.sqlite3`. Depending
on the configured keyset type, it includes:

- the Clear database, including its WAL state when the process is live;
- the root wallet and any other operator-held bearer notes;
- `CLEAR_MASTER_SECRET` for the legacy root-derived keyset;
- `CLEAR_KEY_ENCRYPTION_KEY` for encrypted random keyset secrets;
- `CLEAR_MINT_SERVICE_NSEC` for the stable service identity;
- the operator token and critical configuration;
- the configured root-authority npub and canonical mint URL;
- signed service commissioning and treasurer authorization evidence; and
- treasurer-held keys maintained separately by each treasurer.

Treasurer nsecs must never be collected into the mint backup merely for
convenience.

### Liability rather than Lightning reserve

The recommendation that a Lightning mint remain fully reserved does not map to
a Clear Lightning balance. Instead, each CMU issuer should establish:

- what one unit represents;
- who is obligated to accept or redeem it;
- the maximum authorized outstanding supply;
- any issue, redemption, or final-expiry policy;
- the authority that can change those limits; and
- a signed, auditable statement of issued, retired, and outstanding units.

Clear should never authorize more outstanding units than the issuer's approved
program limit or ability to honor. A limit must be enforced in the mint, not
left solely in an operator runbook.

### Reachability changes risk

An internal-only Mainstay mint has a smaller attack surface than a publicly
reachable Clear mint. A public URL makes the stateless Cashu endpoints and
database-growing operations available to untrusted clients. Deployment policy
must distinguish at least:

- `internal`: reachable only within the local service network;
- `local`: reachable from a controlled LAN or VPN; and
- `external`: reachable through a public TLS gateway.

The stable service npub and keyset IDs do not remove the need to secure every
advertised route.

## Current Safeguards

Clear already provides a useful base:

- SQLite mutations use immediate write transactions for serialized accounting;
- spent proofs are recorded durably and checked before reuse;
- issuance batches are idempotent for an exact quote and output set;
- blinded outputs cannot be signed twice;
- input, output, and state-check arrays are bounded;
- quotes and proofs are bound to an exact keyset and CMU;
- supply is reported per keyset as issued, retired, and outstanding;
- privileged operator endpoints require a bearer token and loopback access;
- signed treasurer actions have expiry and replay protection;
- treasury operations start disabled and require verification plus explicit
  enablement;
- random keyset secrets are encrypted at rest when the key-encryption key is
  configured;
- service identity, mint signing material, and treasurer identity are separate;
  and
- startup rejects several forms of persisted identity and configuration drift.

These controls reduce accounting and custody risk. They do not yet constitute
a production operations profile, automated recovery process, public-edge
defense, or independent security review.

## Priority 0: Required Before Production Value

### Supply and transaction ceilings

`CLEAR_MAX_ORDER` determines the supported binary denominations and currently
also determines the maximum quote amount. Cryptographic denomination depth is
not an operational risk policy. Introduce independent settings such as:

```text
CLEAR_MAX_QUOTE_AMOUNT
CLEAR_MAX_SWAP_AMOUNT
CLEAR_MAX_OUTSTANDING_PER_CMU
CLEAR_MAX_PENDING_QUOTES
```

The limit should be persisted with the CMU policy rather than only inherited
from process environment. A change must identify its authorizing authority,
reason, prior value, new value, and effective time.

Outstanding-cap enforcement must be atomic. Quote authorization should reserve
capacity for authorized but unissued quotes, quote expiry should release that
capacity, and issuance should recheck the invariant in the same transaction
that records signatures and supply changes:

```text
outstanding + reserved-authorized-issuance <= authorized CMU ceiling
```

Swaps do not change outstanding supply. Retirement reduces it. Failed,
expired, or cancelled quotes must not consume capacity indefinitely.

### Backup command and recovery verification

Do not recommend copying only the main SQLite file while Clear is running in
WAL mode. Implement a supported command, for example:

```text
clear-root backup create <destination>
clear-root backup verify <backup>
clear-root restore verify <restored-directory>
```

`backup create` should use SQLite's online backup API or perform a controlled
stop and checkpoint. It should produce a versioned manifest containing:

- backup time and software version;
- schema and commissioning profile versions;
- database integrity-check result;
- service npub and management mode;
- keyset IDs, CMUs, lifecycle states, and public key fingerprints;
- issued, retired, outstanding, and reserved totals per CMU;
- treasury-gate state and current verification identifier;
- the last audit record or audit checkpoint;
- included public evidence and data-file hashes; and
- a list of required secret material that is deliberately stored elsewhere.

`backup verify` must not need signing secrets merely to inspect public metadata
and hashes. A full restore drill must start an isolated Clear instance with the
recovery secrets, reproduce every service and keyset identity, verify encrypted
keyset recovery, reconcile supply, and keep treasury activity disabled until
`clear-root verify` succeeds and an operator explicitly enables it.

Define and test:

- recovery point objective and recovery time objective;
- local snapshot and off-host encrypted-copy frequency;
- retention and deletion policy;
- who can retrieve each secret class;
- restore procedure on a clean host; and
- evidence that the latest scheduled restore drill succeeded.

### Public endpoint protection

Before exposing Clear externally, enforce controls at both the reverse proxy
and application boundary:

- TLS with a deliberately configured canonical external mint URL;
- request-body and header-size limits;
- connection, request, and upstream timeouts;
- concurrency limits;
- separate rate classes for read-only and database-growing operations;
- stricter limits for quote creation, swap, and proof-state requests;
- trusted-proxy configuration so client addresses cannot be spoofed;
- structured logs that omit proofs, bearer tokens, nsecs, and blinded secrets;
  and
- alerting on repeated invalid proofs, duplicate spends, oversized requests,
  and authorization failures.

Proxy controls are useful but insufficient by themselves. Clear should also
have application-level bounds because it may run behind different gateways or
inside a local network where the proxy is bypassed.

IP rate limiting is an abuse control, not an identity or authorization model.
It can affect users behind carrier NAT or shared venue networks and should be
tuned conservatively.

### Pending-quote lifecycle

Unauthenticated clients can create quotes that persist in the database. Add:

- `created`, `authorized`, `issued`, `expired`, and `cancelled` states;
- explicit creation and authorization expiry;
- a maximum count per source and deployment;
- an indexed cleanup process;
- idempotent cancellation and expiry; and
- metrics for total, oldest, and growth rate of pending quotes.

Expired quote cleanup must preserve enough audit evidence to explain any
authorization reservation that was released.

### Monitoring and readiness

`/health` currently establishes process availability. Add a bounded readiness
and operator metrics surface that can report without exposing private material:

- database connectivity, write readiness, and integrity-check age;
- disk free space and recent growth rate;
- database, WAL, spent-proof, quote, and audit-log sizes;
- outstanding and reserved supply per CMU versus its ceiling;
- treasury enabled/disabled state and verification freshness;
- active, inactive, suspended, and commissioning keysets;
- service commissioning and operator-attestation status;
- canonical, internal, local, and external route configuration;
- last successful backup and restore-drill timestamps; and
- software/schema versions and pending migration state.

Alert before disk exhaustion or supply-limit breach rather than only after the
mint becomes unavailable.

## Priority 1: Operational Completeness

### NUT-06 operator information

Extend `/v1/info` with configurable standard metadata:

```text
CLEAR_CONTACTS
CLEAR_MOTD
CLEAR_ICON_URL
CLEAR_TOS_URL
CLEAR_PUBLIC_URLS
```

The response should also include server time and `max_array_length`. The
commissioned operator npub is a natural Nostr contact, but a deployment may
also publish an operational email or other approved channel. `motd` should be
reserved for information wallets need to display, such as maintenance,
suspension, or a redemption deadline.

The implementation version should follow the NUT-06 implementation/version
format, for example `Clear/0.1.0`.

### Reconciliation and signed supply statements

Reconcile independent database views rather than trusting one aggregate:

- authorized quote amounts;
- issued quote amounts;
- issue batches;
- signed outputs;
- spent proofs by reason;
- retirement totals; and
- audit-log totals.

Any mismatch should close the treasury gate and produce a bounded incident
report. Provide a signed public or operator-verifiable supply statement for
each CMU containing the keyset ID, authorized ceiling, issued, retired,
outstanding, reserved, timestamp, sequence, and previous statement ID.

This does not reveal holder balances. It lets issuers, operators, and community
governance compare actual liabilities with authorized program limits.

### Secret custody

Production configuration should fail closed when treasurer-created random
keysets fall back to `CLEAR_MASTER_SECRET` as their encryption key. Require a
dedicated `CLEAR_KEY_ENCRYPTION_KEY`, with separate backup and rotation
procedures, for a hardened profile.

Document secret classes separately:

| Secret | Purpose | Rotation consequence |
| --- | --- | --- |
| `CLEAR_MASTER_SECRET` | Legacy root keyset derivation | Changes the legacy keyset and CMU |
| `CLEAR_KEY_ENCRYPTION_KEY` | Wraps random keyset secrets | Requires controlled rewrapping, not new keysets |
| `CLEAR_MINT_SERVICE_NSEC` | Stable service identity | Requires service-identity rotation and new evidence |
| `CLEAR_OPERATOR_TOKEN` | Local operator API access | Revokes old local API access without changing CMUs |
| Treasurer nsec | Signs treasurer authority requests | Remains outside the mint and follows treasurer rotation policy |

Use a secret manager, protected host file, or hardware-backed mechanism rather
than command-line arguments or plaintext orchestration output. Restrict backup
operators from automatically receiving every secret class.

### Reproducible deployment and upgrades

- Pin images and source dependencies to reviewed releases or commits.
- Record the image digest and configuration fingerprint in the deployment
  manifest.
- Test schema migrations and rollback limitations against a restored copy.
- Take and verify a pre-upgrade backup.
- Keep treasury operations disabled during ambiguous migration or recovery
  states.
- Run post-upgrade commissioning verification before re-enabling treasury
  mutations.
- Exercise wallet interoperability for every supported endpoint and NUT.

Never attach a production database to an unreviewed `main` build merely to test
whether a bug has been fixed.

## Priority 2: Lifecycle and Scale

### Keyset lifecycle and database pruning

Spent-proof state grows over time. The source guidance recommends periodic
keyset rotation and eventual pruning, but Clear's identity rule is stricter:

```text
one exact keyset ID -> one exact CMU
```

Creating a new keyset currently creates a different CMU. It must not silently
move holders into a successor keyset or imply that the balances are equivalent.

Before pruning spent proofs, Clear needs one of two explicit models:

1. retain the keyset-bound CMU model, keep spent-proof state for the full
   redemption obligation, and make any final expiry an explicit issuer policy;
   or
2. introduce a separately authorized durable currency identity with multiple
   keyset epochs and a specified conversion relationship.

Current NUT-02 supports inactive keysets, input fees, and optional final expiry.
Clear advertises these fields but currently uses zero fees and no final expiry.
Adopting either value changes holder and wallet expectations; a nonzero input
fee or final expiry also contributes to current keyset-ID derivation. It must
therefore be designed as identity and policy work, not treated as a cleanup
toggle.

No nullifier may be deleted while Clear remains obligated to accept an
unexpired note from that keyset. A database-maintenance command must prove the
keyset is terminal under its published policy and preserve an auditable pruning
checkpoint.

### Transaction fees

The 2024 source describes Cashu transaction fees as future work. Current
NUT-02 defines `input_fee_ppk`. Clear should not enable fees solely because the
field now exists. For local community credits, authorization limits and local
access policy may be preferable. For a public mint, fees could discourage
self-swapping database-growth attacks, but they also change the keyset ID,
wallet arithmetic, issuer policy, and holder experience.

Any fee proposal requires a new keyset/CMU policy, exact integer arithmetic,
wallet interoperability tests, accounting for collected units, and clear
disclosure through keyset metadata.

### Stronger signing isolation

Application encryption protects keysets at rest but does not protect them from
a process that is compromised while it can decrypt and sign. Higher-assurance
deployments should consider an HSM or remote signer that:

- keeps raw keyset secrets outside the web process;
- enforces active/suspended state and supply ceilings;
- accepts only authenticated, replay-protected signing requests;
- emits an independent audit sequence; and
- fails closed when reconciliation or authorization is stale.

### High availability

Do not create availability by running two writable Clear instances with the
same keyset and independent databases. That permits split-brain issuance and
double spending. A mint cluster requires one synchronous authoritative spent
state, coordinated issuance, fencing, and tested partition behavior.

Until that design exists, prefer rapid restore of one authoritative instance
over unsafe active-active operation.

## Operational Runbook Baseline

### Before first issuance

- Record the canonical mint URL and intended reachability scopes.
- Commission the service identity and verify the operator attestation.
- Record CMU meaning, issuer, treasurer, ceiling, redemption policy, and
  contact method.
- Establish encrypted off-host backups for the database and each required
  secret class.
- Complete an isolated restore drill.
- Run `clear-root verify`, review the evidence, and explicitly enable the
  treasury gate.
- Test issuance, swap, state check, retirement, and recipient redemption.
- Confirm public metadata and limits from a wallet's network context.

### Routine operation

- Monitor health, readiness, supply, reservation, disk, and database-growth
  alerts.
- Review authorization failures, duplicate-spend attempts, and rate-limit
  events.
- Reconcile every CMU on a defined schedule.
- Verify scheduled backups and periodically restore one.
- Publish maintenance or suspension notices through NUT-06 metadata and the
  service's signed communication path.
- Replenish neither supply nor authorization merely to clear an alert; require
  the proper governance action.

### Upgrade

- Close the treasury gate and drain in-flight operator work.
- Record current service identity, keysets, supply, schema, and image digest.
- Create and verify a pre-upgrade backup.
- Apply the reviewed release and migrations.
- Reconcile identities and accounting.
- Run commissioning verification.
- Re-enable the treasury only through an explicit operator decision.

### Incident response

For suspected database corruption, signing-key exposure, unauthorized
issuance, split-brain operation, or supply mismatch:

1. disable treasury mutations immediately;
2. preserve database, WAL, logs, process metadata, configuration fingerprints,
   and signed evidence;
3. avoid deleting spent-proof or audit state;
4. publish a bounded operator notice without exposing bearer material;
5. determine the last known-good reconciliation and backup;
6. restore into isolation and verify identities before advertising it;
7. rotate only the compromised authority or encryption layer whose lifecycle
   is understood; and
8. require explicit governance approval before resuming issuance.

Rotating `CLEAR_MASTER_SECRET` is not incident recovery for an existing legacy
CMU. It creates different signing material.

## Practices That Do Not Transfer Directly

| Source recommendation | Clear interpretation |
| --- | --- |
| Maintain Lightning reserves above ecash liabilities | Enforce authorized CMU ceilings and demonstrate the issuer's ability and obligation to honor outstanding units |
| Choose a dedicated Lightning backend | Not applicable to Clear settlement; relevant only to a separate Lightning-backed mint used by Safebox |
| Rotate derivation paths periodically | Requires a Clear currency/keyset-epoch design; a new keyset currently means a new CMU |
| Charge protocol fees to deter abuse | Now possible in NUT-02, but requires a deliberate Clear policy and new keyset identity |
| Add accounts for rate limiting | Avoid by default; use edge limits, capabilities, and issuer policy without weakening bearer privacy unnecessarily |
| Install the supplied systemd/fail2ban rules | Adapt the principle to the actual Docker, jail, reverse-proxy, firewall, and logging environment |

## Recommended Implementation Order

1. Add independent quote and outstanding-supply ceilings with atomic
   reservation accounting.
2. Add quote expiry, cleanup, and database-growth metrics.
3. Add live-safe backup creation, manifest verification, and restore checks.
4. Add public-edge request bounds and documented reverse-proxy rate classes.
5. Add NUT-06 contacts, URLs, notices, time, and array-limit metadata.
6. Add continuous multi-table reconciliation and signed supply statements.
7. Require dedicated key-encryption material in a production profile.
8. Design CMU lifecycle, final-expiry, and nullifier-pruning semantics.
9. Evaluate fees, isolated signing, and high availability only after those
   invariants are stable.

## Production Readiness Evidence

A future production claim should require evidence that:

- no issuance path can exceed a CMU's authorized ceiling;
- concurrent authorization, issuance, swap, and retirement preserve supply
  invariants;
- database loss within the stated recovery window can be restored without
  identity drift or forgotten spent proofs;
- backups include or reference every required secret without collecting
  treasurer nsecs;
- public endpoints remain bounded under abusive traffic;
- pending quotes cannot grow without expiry or limit;
- wallets receive correct operator, route, limit, keyset, fee, and expiry
  metadata;
- lifecycle transitions fail closed and remain auditable;
- upgrades and restores close the treasury gate until reverified; and
- an independent security review has covered cryptography, accounting,
  authorization, storage, networking, and operational recovery.

Until that evidence exists, Clear should retain its developer-stage and
unaudited warning and should be limited to disposable pilots.
