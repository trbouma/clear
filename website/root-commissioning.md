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

The commissioning workflow is designed to test:

- configuration, database identity, and durable transactions;
- random keyset generation and encrypted key storage;
- public key, CMU, alias, and mint URL discovery;
- quote creation and blinded issuance;
- proof-state checks and exact-amount swaps;
- redemption and retirement;
- supply reconciliation;
- root wallet persistence; and
- complete audit records.

The root uses a dedicated commissioning keyset. It issues test units, exercises
their complete lifecycle, and retires every unit. This proves the shared mint
implementation without adding test supply to an organization's intended CMU.

## Explicit enablement

Verification and enablement are separate decisions:

```bash
clear-root verify
clear-root treasury status
clear-root treasury enable
```

Before enablement, signed treasurer actions fail closed. The mint records who
enabled treasury activity, when it happened, and which successful verification
supported the decision.

The root can close the gate without deleting keysets or ledger history:

```bash
clear-root treasury disable --reason "maintenance"
```

## Readiness can expire

A successful check is not permanent. Database migrations, restores, signer or
key-storage changes, failed reconciliation, and critical routing changes make
verification stale. Clear then requires a new root verification before
treasurer operations can resume.

Changing a friendly currency name or unit alias does not normally invalidate
readiness, although the mint must restart before its new configuration is
advertised.

!!! note "Designed, not implemented"
    `clear-root` already exercises the prototype mint locally. The durable
    readiness record, commissioning keyset, `verify` command, and treasury gate
    described here are accepted requirements for the next implementation
    stage.

[Read the complete commissioning design](https://github.com/trbouma/clear/blob/main/docs/ROOT-COMMISSIONING-AND-TREASURY-READINESS-DESIGN.md){ .md-button .md-button--primary }
[How Clear is governed](governance.md){ .md-button }
[Security](security.md){ .md-button }

