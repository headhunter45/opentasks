# ADR-0017 - Configuration Validation and Repair

Status:
Accepted

Context:

Users may edit configuration files manually.

Configuration drift can occur through:

- Merge conflicts
- Manual edits
- Incorrect overrides
- Upgrades

Decision:

OT shall provide validation and repair capabilities.

Primary commands include:

- ot check
- ot check --fix

Reasoning:

Manual editing is an intentional design goal.

Validation tooling is required to maintain consistency.

Alternatives Considered:

### Disallow Manual Editing

Pros:

- Reduced corruption risk

Cons:

- Contradicts OT philosophy

### Validation Without Repair

Pros:

- Simpler implementation

Cons:

- Increased user work

Consequences:

Positive:

- Better user experience
- Faster recovery
- Improved consistency

Negative:

- More implementation effort
- Repair rules must remain conservative

## Amendments (As-Built)

- **Implemented Configuration Checks (`Validator.validate_configuration` in `src/ot/validation.py`)**:
  - Validates JSON syntax across `.ot/config.json`, `.ot/config.local.json`, and `~/.ot/config.json` (`$OT_USER_HOME/config.json`).
  - Verifies `system.configSchemaVersion == 1` in each layer and checks for cross-layer schema version mismatches (task `a9c5de`).
  - Validates `system.toolVersion` semantic version format and checks that it matches the installed binary version in `.ot/bin/` (`validate_project_version`).
  - Detects protected configuration keys placed in `.ot/config.local.json` (`Severity.WARNING`, fixable) and `~/.ot/config.json` (`Severity.WARNING`, non-fixable).
- **Implemented Configuration Repairs (`Repairer.repair` in `src/ot/validation.py`)**:
  - `ot check --fix` uses `relocate_protected_keys` (`src/ot/config.py`) to deep-merge individual protected dotted keys (`workItem.types`, `workItem.statuses`, `project.name`, etc.) from `.ot/config.local.json` into `.ot/config.json`, preserving unprotected sibling keys and cleaning up empty parent dictionaries (task `a9c5de`).


