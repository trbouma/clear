# Root Commissioning and Treasury Readiness

Status: Accepted target model

## Decision

A Clear mint must prove that its complete operational path works before it
accepts requests from treasurers. `clear-root` is the commissioning and
acceptance tool. It exercises the same treasury action layer that signed
treasurer requests will eventually use.

Treasurer authorization alone is not sufficient to operate a mint. The mint
must also have a current, successful root verification record and an explicit
treasury-enabled state.

```text
mint installed
  -> root bootstrap completed
  -> root verification succeeds
  -> root records readiness
  -> root enables treasury operations
  -> treasurers may submit authorized actions
```

## Goals

- Demonstrate that the mint is operational before delegating routine control.
- Test real cryptographic, database, wallet, and accounting paths rather than
  relying only on process health.
- Make treasury enablement an explicit root decision.
- Fail closed when readiness is absent, stale, or invalidated.
- Preserve durable evidence of what was tested and against which configuration.
- Use the same business logic for root and treasurer actions.
- Allow the root to disable treasury activity immediately without destroying
  keysets or invalidating existing Mint Notes.

## Non-goals

- Claim that commissioning replaces an independent security audit.
- Prove that an issuer will honour its real-world obligations.
- Publish test secrets, bearer proofs, or private configuration.
- Treat one successful verification as permanent evidence of health.
- Allow a remote treasurer to override a disabled or unverified mint.

## Lifecycle

The mint has an explicit commissioning state:

```text
uninitialized
  -> bootstrapped
  -> verification-in-progress
  -> root-verified
  -> treasury-enabled
```

Failure or a critical change moves the mint to a non-enabled state:

```text
verification-in-progress -> verification-failed
root-verified             -> verification-required
treasury-enabled          -> treasury-disabled
```

The state is persisted in the authoritative mint database. Restarting the
process must not silently enable treasury operations or erase the reason they
were disabled.

## Root commands

The intended command surface is:

```text
clear-root verify
clear-root verify --resume <verification-id>
clear-root treasury status
clear-root treasury enable
clear-root treasury disable --reason <text>
```

`clear-root verify` is local-only and uses the same loopback administrative
boundary as other root operations.

`treasury enable` succeeds only when the latest verification record is
successful, current, and compatible with the active configuration. Enabling
treasury operations is separately audited; verification does not enable them
implicitly.

## Verification profile

The root verification profile should check:

1. required configuration and secret availability;
2. database schema, identity binding, transactions, and durable writes;
3. random keyset generation and encrypted secret persistence;
4. restart-safe loading of created keysets;
5. public key, keyset, CMU, alias, and mint URL discovery;
6. quote creation and root authorization;
7. blinded issuance and client-side unblinding;
8. proof-state checking;
9. exact-amount swap and change handling;
10. redemption and permanent retirement;
11. issued, retired, circulating, and outstanding supply reconciliation;
12. root wallet persistence and token encode/decode round trips;
13. complete, ordered audit records for every tested mutation; and
14. public endpoint consistency without exposing root operations remotely.

External NIP-05, relay delivery, and recipient-wallet interoperability may be
reported as separate integration checks. Their failure should not be confused
with failure of the mint's cryptographic and accounting core, but a deployment
may require them before organizational launch.

## Commissioning keyset

Verification uses a dedicated commissioning keyset rather than the intended
program keyset. The root issues test units, exercises the complete lifecycle,
and retires every issued unit before verification succeeds.

The commissioning keyset and its ledger remain visible as audit evidence. They
must be labelled as test-only and must not be presented as an ordinary Clear
balance. A verification run fails if any test amount remains unaccounted for.

Testing a dedicated keyset demonstrates the shared generation, encryption,
issuance, swap, retirement, and accounting implementation without adding test
supply to an organization's intended CMU.

## Durable readiness record

A successful verification atomically records:

- verification ID and profile version;
- Clear software version and build identifier;
- database schema version;
- start and completion times;
- configuration fingerprint;
- key-encryption-key version identifier, never the key itself;
- commissioning keyset ID and CMU;
- each check, result, and non-secret evidence digest;
- issued and retired commissioning totals;
- final audit-log checkpoint; and
- overall result.

The readiness record is evidence, not a bearer credential. It cannot authorize
issuance and contains no keyset secret or spendable proof.

## Invalidation

The following changes invalidate readiness and disable new treasurer actions
until verification succeeds again:

- database schema migration;
- key storage or operational signer change;
- key-encryption-key rotation before successful rewrapping verification;
- authoritative database restore or rollback;
- public mint identity or critical routing change;
- treasury authorization or policy-engine upgrade;
- failed ledger reconciliation;
- failed startup identity check; or
- an explicit root or operator safety action.

Friendly display-name changes do not normally invalidate readiness. Software
may still require a process restart before those values are advertised.

## Treasury gate

Every remotely submitted treasurer action checks the treasury gate before
authorization scopes are evaluated. When the gate is closed, Clear rejects the
request without consuming its nonce or grant.

The response should distinguish operational unavailability from invalid
treasurer authorization without exposing sensitive configuration. Root-local
status output may provide the complete reason and remediation steps.

Disabling treasury activity blocks new supply-changing actions. It does not
erase keysets, invalidate existing Mint Notes, or discard ledger history.
Public proof-state and redemption behavior during a disablement must follow an
explicit incident policy; emergency suspension must not be inferred from a
generic process-health failure.

## Shared action layer

Root verification must not rely on a privileged alternative implementation.
Root and treasurer calls create different authorization contexts and then
invoke the same treasury action:

```text
root-bootstrap authorization -> shared action -> ledger -> audit
signed treasurer authorization -> shared action -> ledger -> audit
```

This is the central commissioning guarantee: the root proves the path that a
treasurer will actually use.

## Current implementation boundary

The current `clear-root` command can inspect, issue, swap, export, send, and
retire test CMUs through the loopback operator API. It does not yet implement
the commissioning state machine, dedicated commissioning keyset, durable
readiness record, or treasury enable gate described here.

Those capabilities must be implemented before Clear enables remote signed
treasurer operations.

