---
title: Inference Credits and User Agency
description: How organizations could use Clear to allocate inference through private, transferable service entitlements rather than individual account balances.
---

# Inference Credits and User Agency

**An organization can allocate access to artificial intelligence without making
every allocation a permanent, named spending account.** Clear could turn an
inference budget into private, transferable service credits that users hold,
share, pool, or assign to agents.

The opportunity is a shift from **an account with permission to consume** to
**a holder with an entitlement to consume**. This brief describes a proposed
application of Clear, not an implemented inference gateway or a claim that
existing model subscriptions permit redistribution.

## The organizational model

An organization might buy access to a large language model (LLM) provider,
operate its own models, or combine both. It could issue a Clear Mint Unit (CMU)
representing access to an inference service it undertakes to provide.

```text
Organization's inference budget or capacity
  -> treasury-authorized credits
  -> users and agents hold and exchange Mint Notes
  -> inference gateway accepts credits
  -> organization supplies inference through its own or contracted models
```

The organization is the issuer. Its gateway is the service acceptance point.
An upstream model provider need not accept Clear or know who originally
received a credit: the gateway could use the organization's provider account.
That account and its credentials would remain under organizational control.
Contractual permission, capacity, and security would need to be established
before offering the service.

The credit is a claim on the organization's specified service, not automatically
a direct claim on its upstream provider. Switching providers or losing a
subscription would not, by itself, resolve the organization's outstanding
obligations to holders.

## What users gain

A researcher could give unused credits to a colleague. A team could pool
allocations for a larger analysis. A member could delegate a bounded amount to
an agent without exposing the organization's billing credentials. An eligible
holder could consume a credit without first establishing an individual billing
account, where the service's access rules permit it.

These are **transferable but purpose-limited entitlements**: credits circulate
between holders but are accepted only by the designated inference service or
other explicitly recognized services. They need not be cash-redeemable, and
their transferability does not imply universal purchasing power.

The issuer can limit total issuance while giving users discretion over how
allocations are redistributed. This can be advantageous where collaborative
work changes faster than centrally administered individual budgets.

## Compared with account credits

| Question | Conventional account-credit design | Proposed Clear design |
| --- | --- | --- |
| Where is the holding recorded? | Balance associated with a service account | Mint Notes held in a wallet |
| How is value reassigned? | Operator updates account balances | Holders transfer notes; recipients swap at the mint |
| Is a named holder account intrinsic? | An account is needed, though it need not always identify a person | No per-holder balance account is required by the proof model |
| How is an agent funded? | Account permissions, subaccounts, or budget controls | A bounded allocation of bearer credits |
| How is recovery handled? | Operator may restore access or adjust balances | Depends on wallet backups and any additional recovery design |
| What does the issuer control? | Account balances and configured account rules | Issuance, mint service, and service acceptance policy |

Account systems can support transfers, pseudonyms, and delegated budgets. The
advantage is not that these functions are impossible otherwise. Clear combines
holder-controlled portability with blind-signature mechanisms that can separate
issuance from spending, without requiring transfers to be recorded as movements
between holder accounts.

## Privacy requires the whole service

Clear's Cashu-derived proofs can support cryptographic unlinkability between
issuance and later presentation. That creates an opportunity to separate
eligibility checks at allocation from routine inference consumption. It does
not make an inference session anonymous by itself.

Logins, network addresses, timing, amounts, prompts, and provider records can
identify or correlate users. A gateway sees requests it processes, and an
upstream provider may receive identifying prompt content. Small or distinctive
allocations can also make activity easier to infer.

A privacy-oriented deployment would need deliberate authentication choices,
minimal logging, appropriate retention rules, and clear disclosure of what the
gateway and provider can observe. Where named access is necessary, Clear may
still improve portability, but the service should not promise anonymous use.

## Define the entitlement before issuing it

An inference credit needs a precise meaning. One possible starting point is a
service purchasing unit spent against a published price schedule. This allows
different models and workloads, but price changes affect how much inference
existing credits purchase.

A fixed token entitlement is another option, but must distinguish model, input,
output, and other priced categories. A compute-based unit needs an equally
clear resource definition. A generic promise of "one inference" leaves too much
variation in request size and cost.

Each CMU's terms should identify the issuer, accepting service, eligible models,
pricing and change policy, any expiry, transfer restrictions, and treatment of
service withdrawal. Separate CMUs must not be presumed interchangeable merely
because one gateway serves them. Outstanding credits should be monitored
against available budget or service capacity; cryptographic validity does not
guarantee the organization can honor them.

## Metering and settlement

Inference cost may be unknown until generation ends. A gateway could accept a
capped prepaid budget, meter consumption, and return unused value as fresh
proofs. Such a workflow requires an application-level design for reservations,
refunds, retries, and interrupted responses; Cashu's proof states alone do not
define an inference billing system.

In particular, the service must prevent duplicate charging and duplicate refunds,
and give users a way to resolve uncertain outcomes without exposing reusable
proof secrets in support records. A payment receipt establishes neither that
an answer was useful nor that the service fulfilled all contractual promises.

Receiving proof data or checking its status is not sufficient acceptance.
Successful mint processing must prevent reuse before the service relies on the
payment. Ordinary Cashu does not provide final offline settlement. An unavailable
mint can therefore interrupt consumption even when the model service is healthy.

## Agency comes with trade-offs

An unrestricted bearer credit can be passed to someone else. Restricting where
it is redeemed does not restrict who can redeem it. A member-only program must
decide whether membership is checked at redemption, whether additional spending
conditions are needed, or whether onward transfer outside membership is acceptable.
Each choice affects privacy and portability.

Likewise, allocating credits to an agent limits the value made available but
does not ensure that the agent uses it wisely or cannot transfer it onward.
Tool permissions, request limits, and service abuse controls remain separate
requirements. Stolen or already-spent credits cannot simply be recovered by
restoring a wallet backup.

An account system may be the better fit where person-specific revocation,
non-transferable quotas, chargebacks, or detailed attribution are essential.
Clear is most attractive when the organization intentionally wants users to
have discretion over a bounded allocation.

## A focused pilot

A limited pilot could use one clearly defined CMU, one gateway, and an explicit
issuance ceiling. It should test transfers and pooling, concurrent spending,
interrupted inference, unused-budget returns, mint outages, and wallet loss.

Evaluation should measure successful redemption, charging errors, refund delays,
available service capacity, and user understanding. Aggregate issuance and
consumption reporting can support budget oversight without automatically
creating a named history of every user's activity. Any assurance report should
state what it verifies and what remains dependent on operator records.

**The policy advantage is user agency within an accountable service budget.**
Clear could let an organization govern issuance and honor redemption while
allowing holders to decide how an allocation circulates. That is a distinct
organizational choice, not merely a different interface for account credits.

## Related briefs

[Where Is the Holding?](where-is-the-holding.md) explains holder-held proofs and
mint-enforced spending. [Cashu, Decoupled](cashu-decoupled.md) explains the
treasury-authorized issuance model underlying this proposal.
