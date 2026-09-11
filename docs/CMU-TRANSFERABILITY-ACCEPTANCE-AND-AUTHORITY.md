# CMU Transferability, Acceptance, and Authority

## Status

This note defines the Clear-level meaning of transferability, acceptance,
authority, and reachability. Applications may use the user-facing availability
states `Instance`, `Local`, and `Across networks`, but those states are derived
from the current sender, recipient, and available routes. They are not
permanent properties of a CMU or new fields embedded in a Cashu token.

## Governing Rule

> Transferability, acceptance, and authority are separate dimensions.

A valid Mint Note is transferable by the Clear protocol. A useful transfer
also requires a delivery path to the recipient and a usable path from the
recipient to the issuing mint. Neither technical transferability nor mint
reachability proves that the recipient recognizes the CMU or trusts the
treasurer standing behind it.

## Independent Dimensions

### CMU identity

The complete keyset ID and canonical `cmu-<keyset-id>` identify the exact
issuance instrument represented by a set of proofs. A friendly name, mint URL,
service `npub`, or treasurer `npub` does not replace that identity.

Keyset rotation creates a new CMU. Changing a route or treasurer does not.

### Protocol transferability

A valid Mint Note is a bearer instrument that can move from one holder to
another. The Clear protocol can encode, encrypt, and deliver that note without
maintaining named holder balances at the mint.

Protocol transferability answers:

> Can control of this bearer instrument be passed to another holder?

It does not promise that an arbitrary recipient can reach the mint, wants the
CMU, or can redeem it under the issuer's policy.

### Operational availability

Operational availability combines recipient delivery and mint reachability
for a particular transfer context. Wallets should present it as:

- **Instance**: usable transfer is confined to members sharing one Mainstay
  instance and its internal services, shown as **Within this instance**;
- **Local**: usable transfer can cross between participating instances over
  deliberately shared local infrastructure without requiring internet access,
  shown as **On the local network**; or
  or
- **Across networks**: the mint and recipient advertise eligible routes beyond
  the sender's local network boundary.

The state is resolved at use time. The same CMU may be available within one
instance, on a local network, or across networks as verified routes are added
or withdrawn. None of those
changes alter the CMU or its outstanding Mint Notes.

An advertised route is not proof of current health. Wallets should report
temporary unavailability separately from the broader availability
classification.

### Acceptance and recognition

Acceptance is a recipient's decision to receive and retain a CMU. Recognition
is the personal, organizational, or community policy that informs that
decision.

Acceptance answers:

> Am I willing to receive this particular issuer-defined unit?

Clear does not infer acceptance from valid proofs, successful delivery, shared
infrastructure, a public endpoint, service commissioning, or another party's
recognition. A wallet may accept an instance-available CMU and decline an `Across
networks` CMU, or make the opposite choice.

### Treasury authority

The active treasurer `npub` identifies who may authorize supply actions for a
CMU under its governing policy. The treasurer's role is distinct from the
currency root, mint operator, Clear service identity, wallet, and network
route.

Authority answers:

> Who stands behind issuance and liability for this CMU under its policy?

One Clear deployment may serve CMUs governed by different treasurers.
Co-location on one server or Mainstay instance establishes neither common
authority nor mutual acceptance.

### Service identity and mint reachability

The Clear service `npub` identifies an addressable mint service independently
of its current endpoints. A keyset-to-service binding identifies the service
responsible for a CMU; scoped endpoints describe how a caller may reach it.

An endpoint may be internal, local, or external and may use HTTP, HTTPS, FIPS,
or another supported transport. A URL in a token remains an advisory
compatibility route rather than the permanent identity of the CMU or service.

### Delivery reachability

The recipient's inbox relays provide paths for encrypted token delivery. Relay
reachability is independent of mint reachability. A token can arrive through a
public relay while naming a mint route that is usable only inside the sender's
environment.

A wallet must establish both paths before describing an ordinary send as
usable:

```text
sender -> eligible recipient inbox
recipient -> correct Clear mint and keyset
```

### Proof state and finality

Receipt is not final confirmation. The receiving wallet must verify or refresh
proofs with the responsible mint and keep pending, confirmed, and rejected
states distinct. Availability does not replace proof-state checks.

## Classification Matrix

| Availability | Acceptance | Treasurer recognition | Meaning |
| --- | --- | --- | --- |
| Instance | Accepted | Recognized | Usable by members within one instance under a known policy |
| Instance | Not established | Unknown | Instance services are usable, but no endorsement is implied |
| Local | Accepted | Recognized | Usable between participating instances on local infrastructure |
| Local | Not established | Unknown | A local route exists, but no endorsement is implied |
| Across networks | Accepted | Recognized | Recipient accepts the CMU and has eligible remote paths |
| Across networks | Not established | Unknown | Technically portable, but not necessarily wanted or trusted |

All combinations are valid. Implementations must not collapse the columns
into a single status such as `trusted`, `public`, or `global`.

## Responsibility Boundaries

Clear owns:

- CMU and proof identity;
- issuance, swap, proof-state, redemption, and retirement rules;
- treasury authorization and mint-side evidence;
- service identity and advertised mint capabilities; and
- the protocol meaning of transferability.

Clear does not own:

- the recipient's acceptance decision;
- a wallet's presentation or recognition policy;
- deployment-specific knowledge that two wallets share local infrastructure;
- recipient inbox relay selection; or
- a guarantee that an advertised route is reachable from every network.

Mainstay or another deployment coordinator may supply scoped local context.
Acorn or another wallet engine resolves recipient and mint routes and applies
the send guard. Safebox Web or another application presents the result and asks
for informed user confirmation.

## User-Facing Language

The preferred wallet labels are:

```text
Availability: Within this instance
```

```text
Availability: On the local network
```

```text
Availability: Across networks
```

Supporting language should remain narrow:

- `Instance`: "Usable by members of this Mainstay instance."
- `Local`: "Usable between participating instances on local infrastructure."
- `Across networks`: "The mint can be reached outside this local system. The
  receiving wallet still decides whether to accept the CMU."

Avoid `global`, `public`, `trusted`, and `widely accepted`. Those terms add
claims that endpoint resolution cannot establish.

## Limited Historical Parallel

The Florentine florin offers a modest historical parallel. Florence issued the
coin under its own public authority, while merchants and institutions beyond
Florence independently recognized it for trade. Its issuing authority,
geographic circulation, and acceptance were connected but not identical.

The analogy is intentionally limited. Medieval coinage was regulated, and the
material verification of a gold coin differs fundamentally from cryptographic
ecash. The relevant lesson is simply that a currency can originate under one
bounded authority and circulate more broadly when others choose to recognize
it. The British Museum records that the florin and Venetian ducat were
recognized and trusted as trading currencies throughout Europe after their
introduction in the 1200s. See the
[British Museum Money Gallery guide](https://www.britishmuseum.org/sites/default/files/2021-05/Money_Gallery_LPG_2020_Room_68.pdf).

## Implementation Direction

1. Keep availability state out of canonical CMU identity and Cashu tokens.
2. Advertise service identity, capabilities, and eligible endpoints separately.
3. Let the wallet derive availability from recipient delivery and mint
   reachability.
4. Stop a send before proof export when usable transfer cannot be established.
5. Keep acceptance and treasury recognition in separate wallet-facing fields.
6. Replace URL-shape heuristics with identity-based multi-route resolution.
7. Preserve the same states and user-facing labels when federation or FIPS
   provides the route.

## Related Notes

- [Mint Notes Vocabulary](MINT-NOTES-VOCABULARY.md)
- [First-Release Treasurer and CMU Authority Model](FIRST-RELEASE-TREASURER-CMU-AUTHORITY-MODEL.md)
- [Root CMU Issuance and Delivery](ROOT-CMU-ISSUANCE-AND-DELIVERY.md)
- [CMU Payment Request Design](CMU-PAYMENT-REQUEST-DESIGN.md)
- [Mainstay Clear Availability, Acceptance, and Authority](https://github.com/trbouma/mainstay/blob/main/docs/CLEAR-TRANSFER-SCOPE-ACCEPTANCE-AND-AUTHORITY.md)
