# ADR-0035 - Non-Destructive Template Upgrades And Sequential Schema Migrations

Status:
Accepted

Context:

Projects customize templates in `.ot/templates/` (ADR-0014, ADR-0022) and store configuration in `.ot/config.json` and `.ot/config.local.json` (ADR-0011, ADR-0013).

During `ot upgrade` (ADR-0015), two open questions (`OQ-0006` and `OQ-0007`) needed resolution:

1. How should `ot upgrade` handle default template updates without overwriting user-customized templates?
2. How should configuration schema versions be represented and migrated across releases?

Decision:

1. **Checksum-Aware Non-Destructive Template Upgrades (`OQ-0006`)**:
   - User-modified templates in `.ot/templates/` shall **never** be silently overwritten during `ot upgrade`.
   - During a transactional upgrade:
     - Any missing default template file is installed automatically.
     - If an existing project template matches the SHA-256 digest of a known unmodified built-in default template from an earlier version, `ot upgrade` may safely update it to the new default template.
     - If an existing project template has been modified by the user and the new release includes an updated default template, `ot upgrade` preserves the user's file untouched, writes the new default alongside it as `<template>.default` (or reports a notice), and lets the user merge changes through normal repository review.
2. **Single Integer `system.configSchemaVersion` & Sequential Migrations (`OQ-0007`)**:
   - Configuration schema versioning uses a single integer key: `system.configSchemaVersion` (starting at `1`).
   - Both `.ot/config.json` and `.ot/config.local.json` (when present) must share a compatible `configSchemaVersion`.
   - Schema changes across releases are applied inside the transactional upgrade staging directory (`perform_transactional_upgrade`) via ordered, pure migration functions (`migrate_v1_to_v2`, `migrate_v2_to_v3`, etc.) before running `Validator(staging).validate_all()`.

Reasoning:

- Preserving user-customized templates honors ADR-0022 (*Template Customization Over Code Customization*) while still allowing untouched default templates to receive upstream improvements.
- A single integer `system.configSchemaVersion` with sequential step functions (`v -> v+1`) is simple to reason about, easy to test deterministically, and executes safely inside the transactional staging directory (ADR-0015).

Alternatives Considered:

### Always Overwrite Templates With Backups

Pros:

- Guarantees latest template placeholders are active

Cons:

- Disrupts project workflows that customized their templates
- Requires users to manually restore their templates after every upgrade

### Dual Schema Version Keys (`configSchemaVersion` + `configSchemaImplVersion`)

Pros:

- Distinguishes minor internal tweaks from breaking schema changes

Cons:

- Unnecessary complexity when additive fields are already backward-compatible and breaking changes can simply increment `configSchemaVersion`

Consequences:

Positive:

- User template customizations are guaranteed safe across upgrades
- Untouched templates stay current automatically
- Deterministic, testable configuration schema evolution

Negative:

- Requires maintaining a registry of historical built-in template checksums and sequential schema migration functions

## Amendments (As-Built)

- **Implementation Tracking**: Implementing checksum-aware template upgrades and the sequential schema migration runner in `src/ot/upgrade.py` is tracked in task `e04754`.
