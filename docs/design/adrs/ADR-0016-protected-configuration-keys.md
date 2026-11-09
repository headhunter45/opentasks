# ADR-0016 - Protected Configuration Keys

Status:
Accepted

Context:

Certain configuration values define shared project behavior.

Examples include:

- Work item types
- Work item statuses
- Work item sizes
- Meeting types
- Identifier formats

Allowing users to override these values locally can create confusion and inconsistent behavior.

Decision:

OT shall classify certain configuration values as protected.

Protected values may still be overridden, but:

- Warnings shall be emitted
- Validation shall report improper placement
- Automatic repair may move values to the correct configuration file

Reasoning:

OT should encourage project-level consistency without preventing local customization.

Alternatives Considered:

### Completely Forbid Overrides

Pros:

- Maximum consistency

Cons:

- Difficult to enforce
- Conflicts with OT's override philosophy

### Allow All Overrides Silently

Pros:

- Simple implementation

Cons:

- Increased user confusion
- Harder debugging

Consequences:

Positive:

- Consistent project behavior
- Actionable warnings
- Better validation

Negative:

- More complex validation logic

## Amendments (As-Built)

- **Protected Key Registry (`src/ot/config.py`)**: `PROTECTED_CONFIG_KEYS` is explicitly defined as:
  - `system`, `system.configSchemaVersion`
  - `project`, `project.name`, `project.description`
  - `workItem.types`, `workItem.statuses`, `workItem.sizes`
  - `meeting.types`
  *(Note: Identifier formats are not configurable keys in `.ot/config.json` and are therefore not part of `PROTECTED_CONFIG_KEYS`.)*
- **Detection & Automatic Repair (`src/ot/config.py`, `src/ot/validation.py`)**: `find_protected_key_violations` flags any protected keys present in `.ot/config.local.json` or `~/.ot/config.json` (`$OT_USER_HOME/config.json`) with a `WARNING` diagnostic during `ot check`, and `ot check --fix` (`Repairer.repair` via `relocate_protected_keys`) deep-merges and relocates individual protected dotted keys from `.ot/config.local.json` into `.ot/config.json` while pruning empty parent dicts (task `a9c5de`). Enforcing protected-key routing in `ot config set` is tracked in task `30dc47`.

