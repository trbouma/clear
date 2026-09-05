---
title: Commissioning a Mint
description: How clear-root proves a mint is operational before treasurers are enabled.
---

# Commissioning a Mint

Clear does not treat a healthy process as proof that a mint is ready for
treasurers. Before routine authority is delegated, the root must exercise the
mint's cryptographic, storage, wallet, and accounting paths and explicitly
enable treasury operations.

```text
install mint
  -> bootstrap locally with clear-root
  -> verify the complete Mint Note lifecycle
  -> record readiness
  -> enable treasury operations
  -> allow signed treasurer requests
```

## What the root verifies

Commissioning profile version 1 tests:

- critical configuration fingerprinting and durable transactions;
- random keyset generation and encrypted key recovery;
- public key and CMU discovery with the test keyset marked inactive;
- quote creation and blinded issuance;
- token encoding, proof-state checks, and exact-value swaps;
- complete retirement and zero-outstanding supply reconciliation; and
- complete audit records.

The root uses a dedicated commissioning keyset. It issues test units, exercises
their complete lifecycle, and retires every unit. This proves the shared mint
implementation without adding test supply to an organization's intended CMU.

## Explicit enablement

Verification and enablement are separate decisions:

```bash
clear-root treasury status
clear-root verify
clear-root treasury enable
clear-root treasury status
```

Before enablement, signed treasurer mutations fail closed. The mint records the
root enable action, when it happened, and which successful verification
supported the decision. The current operator-token boundary does not identify
an individual human operator.

The root can close the gate without deleting keysets or ledger history:

```bash
clear-root treasury disable --reason "maintenance"
```

## Readiness can expire

A successful check is not permanent. Changes to the software or schema version,
advertised mint URL, root keyset, maximum denomination order, root authority,
or key-encryption material make verification stale. Clear then requires a new
root verification before treasurer operations can resume.

Changing a friendly currency name or unit alias does not normally invalidate
readiness, although the mint must restart before its new configuration is
advertised.

Rerunning `clear-root verify` immediately closes the treasury gate. A new
successful result must be enabled explicitly. Failed verification remains
recorded and leaves the gate closed.

!!! warning "Operational evidence, not certification"
    Profile version 1 does not test external relay delivery, recipient wallets,
    root-wallet file persistence, a process restart during the verification
    run, or organizational redemption policy. Commissioning does not replace an
    independent security audit.

[Read the complete commissioning design](https://github.com/trbouma/clear/blob/main/docs/ROOT-COMMISSIONING-AND-TREASURY-READINESS-DESIGN.md){ .md-button .md-button--primary }
[How Clear is governed](governance.md){ .md-button }
[Security](security.md){ .md-button }
