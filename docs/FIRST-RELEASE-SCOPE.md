# First Release Scope

Status: Accepted release boundary

## Release statement

The first Clear release is a single-operator mint host that can support
multiple independent keysets and CMUs on one authoritative deployment.

```text
One operator
└── one Clear deployment
    ├── Keyset A -> cmu-A -> isolated ledger A
    ├── Keyset B -> cmu-B -> isolated ledger B
    └── Keyset C -> cmu-C -> isolated ledger C
```

This is a developer or pilot release, not yet a production-grade or audited
financial service.

## Required capability

### Canonical keyset and CMU identity

- Derive and expose the exact NUT-02 keyset ID.
- Form the protocol unit as `cmu-<keyset-id>`.
- Remove legacy `PTS` and `pts` identifiers from code, APIs, databases, tests,
  and fixtures.
- Treat every keyset as a separate CMU and balance.

### Operator-approved keyset enrollment

- Let the operator configure several keysets in a local registry.
- Allow an externally created keyset secret or protected signer reference to be
  enrolled through an offline administrative path.
- Require explicit operator activation before Clear advertises the keyset,
  accounts for its issuance, or accepts responsibility for redemption.
- Enroll and activate the keyset before any release issuance. The operator must
  not import a keyset and retrospectively assume responsibility for notes that
  were signed outside the authoritative ledger.
- Never accept a raw keyset secret through the public HTTP API.
- Record the keyset descriptor, CMU, friendly name, activation status, database
  location, and signer reference.

For the first release, operator installation of the local registry entry is the
approval boundary. Signed treasury policy and remote HSM enforcement remain
separate hardening work unless they can be completed without destabilizing the
core multi-keyset model.

The safe sequence is:

```text
treasurer or custodian provides keyset
  -> operator validates and activates it locally
  -> Clear creates or verifies its bound ledger
  -> issuance begins through Clear's recorded workflow
```

### Isolated authoritative state

- Give each keyset/CMU its own SQLite ledger initially.
- Bind every ledger to its exact keyset ID and CMU.
- Scope quotes, signed outputs, spent-proof nullifiers, retirement, and audit
  accounting to that keyset.
- Refuse startup when configuration and persisted ledger identity disagree.
- Never aggregate balances or supply totals across CMUs as though they were one
  currency.

### Protocol routing

- Return all active keysets from `/v1/keys` and `/v1/keysets`.
- Resolve `/v1/keys/{keyset_id}` to exactly one configured keyset.
- Route a mint quote by exact CMU.
- Route issuance by the quote's bound keyset.
- Route swap, state-check, redemption, and retirement operations by exact
  keyset ID.
- Reject mixed-keyset inputs and outputs unless a later explicit exchange
  protocol is invoked.

### Operator and holder visibility

- Show the complete CMU, keyset ID, friendly name, and active status.
- Provide supply summaries per CMU.
- Make operator actions auditable and idempotent.
- Keep *Mint Note* as the holder-facing term and *Cashu proof* as the technical
  data-structure term.

### CMU payment requests

- Implement the Clear profile of Cashu NUT-18 without changing its wire format.
- Put the exact `cmu-<keyset-id>` in the request unit field.
- Use a strict mint list containing the accepted Clear endpoint.
- Provide bounded, reusable request and payload codecs for wallet integration.
- Validate request ID, CMU, proof keyset IDs, mint, amount, input fees, and
  single-use state before finalization.
- Treat the payment as pending until the receiver refreshes the proofs.

## Minimum verification

The release test suite should demonstrate:

1. stable standard keyset-ID and CMU derivation;
2. discovery of two or more configured keysets;
3. independent issuance, swap, state check, redemption, and retirement for
   each CMU;
4. rejection of cross-CMU proofs and outputs;
5. isolation of spent-proof state and supply accounting;
6. idempotent issuance and rejection of reused blinded outputs;
7. atomic rejection of concurrent double-spend attempts;
8. correct restart and ledger-identity validation;
9. operator authentication and secret redaction; and
10. interoperability with Acorn or another wallet that supports custom units.
11. NUT-18 request and payment-payload round trips for an exact CMU.

## Operational release work

- Document installation, configuration, keyset enrollment, backup, restore,
  rotation, suspension, and incident recovery.
- Add explicit database schema versioning and migrations.
- Define secure file permissions and secret-loading guidance.
- Add structured logs without bearer secrets, keyset secrets, or operator
  tokens.
- Bound request sizes, apply rate limits, and document TLS/reverse-proxy
  requirements.
- Build and install the package from a clean environment.
- Run unit, concurrency, restart, API, and live wallet interoperability tests.
- Clearly label the release experimental and unaudited.

## Explicitly deferred

The first release does not include:

- mint clusters;
- mint-to-mint nullifier reservation or spent-state synchronization;
- issuance of one CMU across independently operating databases;
- quorum or partition handling;
- automatic exchange between CMUs;
- implicit equivalence across keyset rotation; or
- production claims before independent security review.

These are candidates for the next release after the single-deployment,
multi-keyset model is stable.

## Definition of done

The first release is ready when one operator can safely configure at least two
keysets, expose both through one Clear service, independently issue and redeem
their Mint Notes, restart without identity drift, and demonstrate that no
operation can accidentally combine or double-spend across their CMUs.
