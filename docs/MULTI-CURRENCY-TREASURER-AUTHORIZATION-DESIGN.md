# Multi-Currency Treasurer Authorization Design

Status: Proposed

## Summary

Clear should host multiple independent policy domains without becoming the
custodian of treasurer private keys. Each domain has its own durable governance
identity, operational keysets and keyset-bound CMUs, treasury policy, ledger,
and authorized treasurer public keys.

A treasurer keeps their Nostr private key (`nsec`) entirely to themselves.
Clear knows only the corresponding public key (`npub`) and verifies signed,
single-use authorization events for actions such as Mint Note issuance,
redemption, and retirement.

The target model is:

> One Clear service, many isolated currency domains, independently governed by
> signed treasurer policies.

## Goals

- Support multiple Clear currencies in one public service.
- Keep every currency's keys, policy, and accounting independent.
- Let different treasurers govern different currencies without cross-access.
- Never ask Clear to receive, derive, store, or transmit a treasurer `nsec`.
- Support one-of-one treasury control initially and threshold approval later.
- Preserve signed evidence of who authorized each supply-changing action.
- Keep standard Cashu circulation and proof validation separate from treasury
  governance.
- Make replay, stale authorization, and cross-currency authorization fail
  closed.
- Keep every `cmu-<keyset-id>` balance distinct, including CMUs authorized by
  the same currency root.

## Non-goals

- Cross-currency balance aggregation.
- Automatic exchange between currencies.
- Automatic equivalence between old and new keysets.
- Treating a friendly currency name as cryptographic identity.
- Giving treasurers direct access to operational mint signing keys.
- Publishing private treasury activity to public relays by default.
- Defining the organization's legal, accounting, or redemption policy.

## Authority model

Clear needs three separate forms of authority and a fourth operational identity
for receiving instructions. These keys must not be interchangeable.

## Governance roles

Clear distinguishes governance authority, infrastructure operation, and
routine treasury action. Control of one role must not automatically grant the
powers of another.

### Currency root authority

The currency root authority governs the currency itself. It establishes the
durable currency identity and signs policy events that:

- appoint, replace, or remove treasurers;
- set approval thresholds, scopes, and issuance limits;
- authorize or replace the currency's mint-service identity and relay set;
- authorize operational Cashu keysets; and
- define policy succession and emergency governance rules.

The root authority is expected to act infrequently. Its private key should be
offline or hardware-backed and must not be stored on the running mint.

### Mint operator

The mint operator runs the Clear service, database, relay connections,
deployment, monitoring, backups, and recovery procedures. The operator installs
root-signed policies and restarts Clear, but cannot create a valid policy or
change currency authority merely by editing configuration.

Operating the server is an administrative responsibility, not authority to
issue currency. A compromised operator can disrupt service or misuse any
software-held operational keys, but policy verification must prevent the
operator from appointing treasurers or changing governance without a valid
currency-root signature.

### Treasurers

Treasurers exercise routine authority delegated by the active policy. They sign
individual Mint Note issuance, redemption, and retirement authorizations within
their scopes, limits, and approval threshold. They cannot appoint themselves,
alter the threshold, replace the mint identity, or redefine the currency.

An ordinary treasurer holds only their authorization key. A policy may also
appoint a treasurer as a **keyset custodian** or **delegated operational
signer**. That separate role controls a Cashu keyset secret and can bring the
keyset to an operator-approved Clear deployment. Because the keyset secret can
create valid Mint Notes, this delegation carries issuance power beyond the
ordinary treasurer role and must be explicit in policy.

### Role overlap

In a small organization, one person may initially serve as root custodian,
mint operator, and treasurer. The roles and keys must remain separate even when
the same human fills them. This allows responsibilities to be separated later,
limits accidental key use, and leaves an auditable record of which authority
was exercised.

```text
Currency Root Authority
  | signs governance policy
  v
Mint Operator installs policy and restarts Clear
  | Clear verifies and enforces policy
  v
Treasurers authorize Mint Note issuance and retirement
```

### Signing responsibilities

| Role or component | Key location | What it signs |
| --- | --- | --- |
| Currency root authority | Offline or hardware-backed | Governance policies, treasurer membership, mint-service identity, and operational keyset authorization |
| Treasurer | Treasurer wallet or hardware signer | Individual Mint Note issuance and retirement authorizations |
| Keyset custodian or delegated signer | HSM, remote signer, or protected offline system | Blinded Cashu outputs for one explicitly authorized keyset |
| Mint service | Running Clear service or protected signer | Receipts, responses, and encrypted communication events |
| Operational Cashu signer | Isolated mint signer, eventually HSM-backed | Blinded Cashu outputs for its authorized keyset |

The mint operator has no inherent signing key in this authority model. The
operator may have deployment credentials, but those credentials do not confer
currency-root or treasury authority.

## Cryptographic identities

### Currency root key

The currency root defines the durable governance identity and authorizes
treasury policy and operational keysets. It should normally be offline or
hardware-backed.

The root does not define one protocol unit spanning its keysets. Each
operational keyset defines its own Clear Mint Unit:

```text
cmu-<keyset-id>
```

Keyset rotation therefore creates a new CMU. The root may authorize an explicit
exchange or migration from notes in an old CMU to notes in a new CMU, but root
continuity does not make the notes automatically equivalent.

### Treasurer identity

A treasurer is identified by a Nostr public key. The currency policy records
the normalized 32-byte hexadecimal public key; applications may display the
equivalent `npub`.

The treasurer keeps the corresponding `nsec`. Clear never needs it.

The ordinary treasurer `nsec` authorizes administrative actions but does not
sign Cashu proofs. A treasurer who is separately entrusted with a keyset secret
is acting as a keyset custodian or delegated operational signer and can create
cryptographically valid Mint Notes for that CMU.

### Operational mint signer

Operational denomination keys issue Mint Notes by signing blinded Cashu
outputs and validate the resulting proofs. They should be replaceable keyset
epochs authorized by the currency root. Every epoch retains its own CMU.

Compromise of an operational signer can allow inflation outside the normal
treasury workflow. Key isolation, short epochs, issuance limits, audit records,
and eventually an HSM-backed policy-enforcing signer are therefore still
required even when treasury authorization is strong.

### Portable keyset enrollment

A keyset need not originate inside the Clear instance that serves it. A keyset
custodian may request enrollment of an existing keyset by providing its public
descriptor, proving control, and supplying either a protected signer reference
or, for development-only deployments, the keyset secret through an approved
offline installation path. The mint operator must explicitly approve and
activate the keyset under a root-signed policy before the instance advertises
the CMU or accepts responsibility for its notes.

Operator approval is meaningful as policy admission, accounting acceptance,
and a redemption commitment. It is not a cryptographic veto over a person who
already possesses the raw keyset secret. Hard two-party control requires the
secret to remain inside an HSM or remote signer whose policy requires both a
valid treasury authorization and operator approval before signing.

The enrollment transaction should record at least the complete keyset public
descriptor, derived CMU, policy version, custodian identity, authorized mint
service identities and endpoints, activation time, signer reference, and the
initial issuance checkpoint.

### Mint service identity

Each currency has its own Nostr service identity and one or more home relays.
The service publishes its `npub` as the destination for treasury instructions
and holds the corresponding `nsec` securely so it can decrypt requests and sign
receipts.

The mint service identity is a communication key. It is not the currency root,
a treasurer identity, or an operational Cashu signing key. Compromise may expose
instructions or permit forged acknowledgements, but must not independently
authorize issuance or produce valid Cashu proofs.

Treasury instructions are signed by authorized treasurers, encrypted to the
currency-specific mint `npub`, and delivered through a configured home relay.
The relay is untrusted transport and storage: it cannot create a valid
instruction. Multiple relays or a direct HTTP submission path may provide
alternate delivery without changing the authorization rules.

The mint service key may be rotated without changing the durable currency
identity or invalidating circulating proofs. The active service `npub` and
relay set should be authenticated by the currency policy or a root-signed
service record.

## Currency domain

Each currency domain contains:

```text
CurrencyDomain
├── currency root public key and fingerprint
├── friendly name and policy reference
├── mint service public key and home relays
├── treasury policy and policy version
├── authorized treasurer public keys
├── active and historical operational keysets
│   └── cmu-<keyset-id> for each keyset
├── independent currency ledger
├── used authorization IDs and nonces
└── issuance, retirement, and audit history
```

The friendly name can change without changing the governance domain. The root
fingerprint identifies policy continuity. The logical mint, complete
`cmu-<keyset-id>`, and authenticated set of service endpoints identify and
route a Mint Note balance. These identifiers serve different purposes and must
not be collapsed.

## Treasury policy

A versioned treasury policy should define:

- the currency root identifier;
- the policy version and activation time;
- authorized treasurer public keys;
- the approval threshold;
- action scopes granted to each treasurer;
- optional per-action or time-window issuance limits;
- authorization lifetime limits; and
- the policy replacement and emergency-revocation rules.

An initial policy may be:

```yaml
version: 1
threshold: 1
treasurers:
  - pubkey: <32-byte hex public key>
    scopes: [issue, retire]
```

The data model should support a later policy such as:

```yaml
version: 3
threshold: 2
treasurers:
  - pubkey: <finance officer public key>
    scopes: [issue, retire]
  - pubkey: <board chair public key>
    scopes: [issue, retire, keyset_rotate]
  - pubkey: <community custodian public key>
    scopes: [issue, retire]
```

The currency root should sign policy creation and replacement. This prevents a
compromised treasurer credential from adding a new treasurer or lowering the
approval threshold.

## Signed policy event and local activation

Each currency needs a root-signed Nostr policy event that declares its
authorized treasurers. The complete event is stored as JSON and explicitly
installed in the mint configuration. Installing or changing it is a deliberate
deployment operation: update the configured policy-event file and restart the
mint. Clear must not provide a live administrative endpoint that can silently
change treasury membership.

```yaml
currencies:
  community-mint-units:
    policy_event_file: "./policies/community-mint-units-v1.json"
```

The policy file is a complete NIP-01 event whose `pubkey` is the currency-root
public key. Its `content` is compact canonical JSON containing the currency,
policy version, previous-policy event ID, mint service identity and relays,
threshold, treasurer public keys, scopes, and limits. The Nostr event ID and
signature authenticate the policy; no additional signature field is needed.

On first initialization, Clear must:

1. Decode and normalize each `npub` to its 32-byte hexadecimal public key.
2. Validate that the threshold can be satisfied by distinct configured
   treasurers with the required scopes.
3. Persist the complete signed event, policy version, and event ID in the
   currency ledger.
4. Bind the initialized ledger to the currency root and the authorized keysets
   and CMUs it recognizes.

After initialization, the persisted event remains the authority against which
the configured event is evaluated. Changing the configured JSON file and
restarting Clear is the only deployment mechanism, but replacing the file
alone does not grant authority. A successor event must carry a valid
currency-root signature, use the next permitted policy version, identify the
same currency root and previous event ID, and satisfy all policy invariants.

On startup, Clear compares the configured and persisted policy:

- an exact match starts normally;
- a valid, root-signed successor is recorded and activated atomically;
- an unsigned, stale, skipped, malformed, or wrong-currency policy stops
  startup with a clear policy-mismatch error; and
- removing the configured policy-event file after initialization also stops
  startup.

Adding or removing a treasurer, changing scopes, or changing the threshold
therefore requires a short policy deployment ceremony:

1. The currency root authority prepares or reviews the complete successor
   policy content.
2. The currency root authority creates and signs its Nostr event with the
   offline root key.
3. The mint operator stops the Clear currency service.
4. The mint operator backs up the current currency ledger and configuration.
5. The mint operator installs the signed event JSON and restarts Clear.
6. The root authority and mint operator confirm the active policy version and
   event ID from Clear's health or information endpoint.

### Treasurer key replacement

Replacing an authorized treasurer `npub` should be routine even though policy
activation remains deliberate. A guided command should copy the current
policy, replace exactly one public key, increment the policy version, preserve
the treasurer's scopes, validate the resulting threshold, and write an
unsigned successor event template:

```text
clear policy replace-treasurer \
  --policy community-mint-units-v1.json \
  --old-npub npub1old... \
  --new-npub npub1new... \
  --output community-mint-units-v2.unsigned.json
```

Before the successor can be signed, the new treasurer key should sign a
one-time acceptance challenge containing the currency ID, old public key, new
public key, and successor policy version. This proof of possession catches an
incorrect or unusable replacement key. The currency root then signs the full
successor policy; possession of the old treasurer key is helpful evidence but
is not required, because key loss or compromise is a primary reason for
replacement.

The currency root authority signs the template. The mint operator installs the
resulting `community-mint-units-v2.json` and restarts Clear using the normal policy
deployment ceremony. Activation immediately removes the old key's authority.
Unconsumed authorizations and pending approvals from the previous policy
version become invalid and must be recreated under the new policy. Already
consumed authorizations remain valid historical evidence and continue to
verify against the retained older policy.

The replacement command must refuse ambiguous edits, including a missing old
key, a new key already present in the policy, an invalid `npub`, or a resulting
policy whose threshold cannot be satisfied. It must display the old event ID
and prospective policy digest for human confirmation before writing the
successor file.

The mint never receives the currency-root private key. It receives only the
signed policy event and root public key needed for verification. The ledger
retains every prior policy version so historical authorizations can be checked
against the policy active when they were consumed.

For a single-currency development instance, Clear may initially expose:

```text
CLEAR_TREASURER_NPUBS=npub1...,npub1...
CLEAR_TREASURY_THRESHOLD=1
```

These settings are suitable only for an early single-currency development
bootstrap. The durable design uses the signed event JSON and restart ceremony;
environment variables must not remain an alternate path for changing an
initialized policy. No treasurer or currency-root `nsec` may appear in mint
configuration, the currency registry, or the Clear database.

### Storage and relay publication

The complete policy event is local-first. Clear keeps three authoritative or
recoverable copies:

1. The explicitly installed signed event JSON in deployment configuration.
2. An immutable copy in the currency ledger after successful activation.
3. A protected backup outside the running mint.

Relay delivery must never be an activation mechanism. Clear must not discover
the latest policy on a relay and activate it automatically. A policy found on a
relay can be downloaded and inspected, but an operator must still install the
event locally and restart the mint.

Publishing the complete policy is optional because it can reveal treasurer
public keys, thresholds, scopes, mint-service identity, relay topology, and the
timing of governance changes. An organization may explicitly mirror the full
event to a private relay or local Spurline instance for continuity, recovery,
or audit.

Public transparency should use separate records by default:

- a **policy commitment** containing the currency ID, policy version, policy
  event ID or hash, and activation time; and
- a **service record** containing the public mint identity, endpoints, relay
  hints, active Cashu keysets, and the CMU defined by each keyset.

Neither record grants authority, and neither substitutes for the locally
installed complete policy event. The initial implementation should store the
full policy locally and make all relay publication an explicit opt-in action.

## Signed authorization envelope

Clear should authorize a canonical action payload rather than a loosely worded
message. The signed envelope needs to bind every security-relevant field:

```json
{
  "authorization_id": "<random UUID>",
  "currency": "<currency-root-fingerprint>",
  "policy_version": 3,
  "action": "issue",
  "amount": 500,
  "unit": "cmu-<keyset-id>",
  "subject": "<quote ID or retirement commitment>",
  "nonce": "<32 random bytes encoded as hex>",
  "created_at": 1786636800,
  "expires_at": 1786637100,
  "reason": "Community emergency allocation"
}
```

The canonical payload is hashed. Each approving treasurer signs the same
payload hash in a Nostr event. Since a Nostr event ID includes the signer's
public key, threshold approvals will have different event IDs but share the
same `authorization_id` and payload hash.

The final event kind should be allocated after interoperability discussion.
Until then, Clear should use an explicitly experimental kind and versioned
payload. NIP-98 may protect HTTP transport, but transport authentication alone
is insufficient: the durable authorization must bind the currency, action,
amount, subject, policy version, nonce, and expiry.

## Verification rules

Clear accepts an authorization only when all of these checks pass:

1. The Nostr event ID is correctly derived.
2. The Schnorr signature is valid for the event public key.
3. The public key is an active treasurer in the cited policy version.
4. The treasurer has the required action scope.
5. The currency, unit, quote, amount, and action match the pending operation.
6. The authorization has not expired and is not unreasonably far in the future.
7. The `authorization_id`, nonce, and event ID have not been consumed.
8. Every threshold signature covers the same canonical payload hash.
9. The number of distinct valid treasurer approvals meets the policy threshold.
10. Currency and time-window issuance limits remain satisfied.

Authorization consumption and the supply-changing ledger transaction must
commit atomically. A successful authorization cannot be replayed, and a failed
mint or retirement transaction must not leave ambiguous partial state.

## Issuance flow

```text
Wallet               Clear                 Treasurer
  |                     |                       |
  |-- request quote --->|                       |
  |<-- pending quote ---|                       |
  |                     |-- action payload ---->|
  |                     |<-- signed approval ---|
  |                     |-- verify policy ------|
  |                     |-- authorize quote ----|
  |-- blinded outputs ->|                       |
  |<-- blind signatures-|                       |
```

Clear records the quote, canonical authorization payload, all contributing
treasurer events, policy version, issued amount, output commitment, and ledger
transaction reference.

When the authorized treasurer is also the delegated keyset signer, the flow may
route blinded outputs to that signer after Clear approves the request. The
resulting issuance must still be committed to the authoritative ledger before
the signatures are released. A signer that releases signatures first creates
an unaccounted issuance window.

## Mint clusters and issuance across instances

A **mint cluster** is an operator-approved and policy-authorized group of Clear
instances exposing the same keyset and CMU as endpoints of one logical mint.
This supports geographic distribution, operator redundancy, and treasurer
interaction with more than one mint instance.

The treasurer, acting within the active policy, proposes or selects the other
mint instances that participate in the cluster. The mint operator must approve
the local instance's membership and connectivity. The resulting signed cluster
manifest must identify the cluster, CMU, member service identities and
endpoints, state-consistency mode, and membership version.

Every member must share or coordinate one authoritative state for:

- consumed treasury authorizations and nonces;
- issuance quotes and signed-output commitments;
- outstanding and retired supply accounting;
- spent-proof nullifiers; and
- keyset activation, suspension, and revocation.

Strong consistency is mandatory for supply-changing and proof-consuming
operations. A shared transactional database, a single-writer service, or a
consensus-backed state machine are acceptable architectural directions. Loose
eventual replication is not sufficient because two isolated instances could
authorize duplicate issuance or redeem the same Mint Note.

```text
Treasurer / delegated signer
          |
          v
 Operator-approved mint cluster
     /          |          \
Instance A  Instance B  Instance C
     \          |          /
      authoritative shared state
```

If instances do not share this state, each must use its own keyset. Those
keysets define different CMUs even when the instances have the same operator,
treasurers, friendly name, or currency root.

### Mint-to-mint double-spend protocol

Where cluster members do not share one transactional database, Clear needs an
authenticated mint-to-mint protocol. The protocol should use the proof's Cashu
`Y` value as the nullifier and provide at least:

- `GET /cluster/v1/state/{Y}` to inspect `UNSEEN`, `RESERVED`, or `SPENT`;
- `POST /cluster/v1/reservations` to atomically reserve one or more nullifiers
  for a short-lived transaction ID;
- `POST /cluster/v1/commits` to mark a reserved set permanently spent;
- `POST /cluster/v1/releases` to release an expired or aborted reservation;
- a monotonic change feed or snapshot protocol for repair and catch-up; and
- signed membership and state responses bound to the cluster ID, CMU, member
  identity, request ID, and expiry.

A redeeming instance must consult the members required by the active cluster
policy before accepting a note. In the safest initial design, every active
member must acknowledge the reservation. A later quorum design requires a
consensus protocol that prevents two partitions from forming independent
spending quorums; a simple majority of HTTP replies is not sufficient by
itself.

```text
Redeeming mint       Cluster peers       Authoritative state
      |-- reserve Y ----->|                      |
      |<-- acknowledgements / conflict ---------|
      |-- validate and commit Y ---------------->|
      |<-- committed checkpoint ----------------|
```

The change feed can synchronize historical double-spend state and restore a
recovering member. It must not replace the synchronous reservation decision on
the live redemption path. If the required members or authoritative writer are
unavailable, the mint fails closed and does not redeem the note.

Issuance authorization consumption requires the same class of coordination.
Otherwise the same authorization could be accepted independently by two
cluster members even if their spent-proof sets later converge.

## Clear Treasury CLI

Clear should include a separately installable `clear-treasury` package and
command for organizational treasurers. It may live in the Clear repository
while retaining a strict dependency boundary from the mint service.

The Treasury CLI holds or delegates access to the treasurer `nsec`, manages
currency and CMU profiles, creates blinded outputs, signs authorizations,
tracks pending threshold approvals, verifies mint responses, and constructs
returned Cashu tokens containing Mint Notes locally. It must never import the
mint database, operational signing keys, or an internal authorization bypass.

For a one-of-one policy, the initial experience should be:

```text
clear-treasury issue \
  --cmu cmu-<keyset-id> \
  --amount 500 \
  --reason "Community allocation"
```

The CLI generates proof secrets locally, commits the authorization to the
corresponding blinded outputs, submits the encrypted signed instruction, and
unblinds the mint response. Clear therefore never learns the final bearer proof
secrets. The resulting Mint Notes belong to exactly one logical mint and CMU
and must not be combined with notes from another logical mint or CMU.

Threshold workflows separate request creation, approval, and claiming:

```text
clear-treasury issue-request --cmu cmu-<keyset-id> --amount 500
clear-treasury approve <request-id>
clear-treasury claim <request-id>
```

The requesting Treasury wallet retains the proof secrets until enough valid
approvals have arrived. Tokens must not be published in relay events or normal
logs; interactive display and an explicit protected output file are suitable
initial export mechanisms.

## Redemption and retirement flow

Redemption for retirement must bind the approval to a commitment over the exact
Mint Note proof set, not merely an amount. Clear should calculate a canonical
commitment from the currency ID, CMU, proof `Y` values, amounts, and intended
reason.

```text
Organization          Clear                 Treasurer
  |-- Mint Note proofs ->|                       |
  |                     |-- retirement digest ->|
  |                     |<-- signed approval ---|
  |                     |-- verify threshold ---|
  |                     |-- mark proofs spent --|
  |<-- retired result --|                       |
```

The proof nullifiers, authorization consumption, retirement entry, and supply
change must be one atomic transaction.

## Privacy and publication

Treasury authorizations can reveal amounts, timing, organizational activity,
and relationships. Clear should store signed authorization events in the local
currency ledger and should not publish them to public relays by default.

An organization may later choose to publish:

- signed aggregate issuance and retirement summaries;
- policy documents and policy changes;
- keyset activation and revocation events; or
- commitments to a private audit log.

Publication policy is separate from authorization validity.

## Multi-currency runtime

The first multi-currency runtime should use a public registry with isolated
currency contexts:

```text
ClearRouter
├── Currency A -> process/store A -> database A -> signer A
├── Currency B -> process/store B -> database B -> signer B
└── Currency C -> process/store C -> database C -> signer C
```

Separate SQLite files are preferred initially. A shared database server may be
introduced later, but every table and uniqueness constraint must remain scoped
by immutable currency identity.

The registry contains public configuration and signer references, not root or
treasurer private keys. A hosting administrator should not gain treasury
authority merely by operating the router.

This local multi-currency router is different from a mint cluster serving one
CMU. A mint cluster is a distributed deployment of one logical mint and
requires synchronously coordinated authoritative state; the router isolates
independent keysets and ledgers within one runtime.

Public Cashu requests route by protocol unit and keyset ID. Administrative
requests are explicitly scoped to a currency path, for example:

```text
POST /v1/currencies/{currency_id}/authorizations
GET  /v1/currencies/{currency_id}/authorizations/{authorization_id}
POST /v1/currencies/{currency_id}/quotes/{quote_id}/approve
POST /v1/currencies/{currency_id}/retirements
```

The final API should avoid endpoints with global operator authority.

## Ledger additions

Each currency ledger needs records equivalent to:

- `treasury_policies`
- `treasury_policy_members`
- `authorization_payloads`
- `authorization_signatures`
- `consumed_authorizations`
- `operational_keysets`
- `keyset_enrollments`
- `authorized_service_instances`
- `mint_quotes`
- `signed_outputs`
- `spent_proofs`
- `retirements`
- `audit_log`

The ledger should retain the original signed events and canonical payload bytes
needed for independent verification.

## Threat model

### Compromised treasurer key

An attacker can approve actions within that treasurer's scopes. Threshold
policies, issuance ceilings, short authorization lifetimes, revocation, and
clear audit visibility limit exposure. Other currencies remain unaffected.

### Compromised operational keyset

An attacker may create valid proofs without treasury approval. Rotation limits
future exposure but does not automatically distinguish already forged proofs.
Non-exportable signing keys and signer-enforced conservation or authorization
limits are the preferred controls.

### Compromised currency root

An attacker may replace policy or authorize malicious keysets. The root should
remain offline or hardware-backed and should be used only for infrequent policy
and keyset lifecycle actions.

### Compromised Clear host

The host may censor requests, hide state, roll back a ledger, or misuse any
software-held operational key. Durable backups, rollback detection, external
audit commitments, process isolation, and hardware signing boundaries are
required before production use.

## Migration from the prototype

The current Clear prototype has one keyset-bound unit using legacy identifier
syntax, one SQLite ledger, and a global operator token. Migration should occur
before any meaningful Mint Notes are issued.

### Phase 1: Signed single treasurer

- Replace the global operator token with one configured treasurer `npub`.
- Add canonical signed issue and retire authorizations.
- Add replay protection and signed authorization storage.
- Keep one currency and threshold `1`.

### Phase 2: Durable governance root and explicit CMU lifecycle

- Introduce an offline currency root identity.
- Form each protocol unit as `cmu-<keyset-id>`.
- Add root-signed treasury policy and keyset authorization.
- Require explicit issuer policy for exchange or migration between keyset-bound
  CMUs; never imply equivalence from a shared root.
- Treat existing prototype databases as development-only and non-migratable
  unless an explicit conversion tool is written.

### Phase 3: Multiple isolated currencies

- Add the public currency registry and router.
- Run separate stores and signer contexts per currency.
- Remove every remaining global administrative operation.

### Phase 4: Threshold treasury and hardware signing

- Accept multiple signatures over one authorization payload.
- Enforce policy thresholds and role scopes.
- Move operational signing keys into an HSM-backed or remote signer boundary.
- Add issuance limits, keyset epochs, revocation, and auditable summaries.

## Open questions

- Which experimental Nostr event kind should carry Clear authorization?
- Should policy documents be Nostr events, OpenETR records, or both?
- How should root-signed operational keyset certificates be encoded?
- What clock and expiry tolerance is acceptable during disconnected operation?
- How should emergency revocation work when the wider network is unavailable?
- Which authorization details can be published without exposing private
  organizational activity?
- Can the intended HSM enforce signing budgets or proof-conservation rules, or
  only protect raw key material?
- What explicit migration evidence is required when replacing a compromised
  keyset?

## Decision direction

Clear should proceed with signed, currency-scoped treasurer authority and no
treasurer private-key custody. The first implementation should prove one
treasurer `npub` with threshold `1`, while the data model and signed payload
format should be ready for multiple independent currencies and threshold
approval.
