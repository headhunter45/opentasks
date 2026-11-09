# ADR-0023 - First Class Validation And Repair

Status:
Accepted

Context:

OT encourages users to edit files directly.

Direct edits may create:

- Broken references
- Invalid statuses
- Invalid identifiers
- Invalid relationships

Decision:

Validation and repair are first-class responsibilities of the OT toolset.

Commands such as:

- ot check
- ot check --fix

are core functionality rather than optional utilities.

Reasoning:

Manual editing is a design goal.

Validation is required to support that goal safely.

Alternatives Considered:

### Restrict Direct Editing

Pros:

- Fewer errors

Cons:

- Conflicts with repository-native philosophy

### Detection Only

Pros:

- Simpler implementation

Cons:

- More user effort

Consequences:

Positive:

- Safe manual editing
- Consistent project state
- Better user experience

Negative:

- Additional implementation effort
- Requires careful repair logic

## Amendments (As-Built)

- **Implemented Diagnostics & Exit Codes (`src/ot/validation.py`, `src/ot/cli.py`)**:
  - `ot check` runs `Validator.validate_all()` across `filesystem`, `config`, `version`, `work_item`, and `merge_conflict` categories, emitting `ERROR`, `WARNING`, and `INFO` severities (with `--json` support for machine-readable output).
  - Exit code is `0` when no `ERROR` diagnostics are present and `2` when one or more `ERROR` diagnostics are found.
  - Current `work_item` checks cover: unresolved merge conflict markers (`<<<<<<<` / `>>>>>>>`), valid & unique UUIDv4s, configured `type` (`ERROR`), configured `status` (`ERROR`), configured `size` (`WARNING`), self-dependencies (`WARNING`, fixable), and broken `parent` / `dependencies` target UUID references (`WARNING`).
- **Implemented Automatic Repairs (`ot check --fix`)**:
  - Recreates missing required directories (`.ot`, `.ot/tasks`, `.ot/templates`, `.ot/meetings`).
  - Moves protected configuration keys from `.ot/config.local.json` to `.ot/config.json`.
  - Removes self-dependencies from WorkItems.

