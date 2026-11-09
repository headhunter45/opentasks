# ADR-0029 - .ot Directory As Canonical Tool Root

Status:
Accepted

Context:

OT requires a predictable location for:

- Configuration
- Work items
- Templates
- Meetings
- Installed tool versions

Decision:

The .ot directory shall be the canonical OT project root.

All OT-owned project data shall exist within or beneath .ot unless explicitly relocated through configuration.

Reasoning:

A single root directory simplifies:

- Discovery
- Validation
- Upgrades
- Migration
- Backup

Alternatives Considered:

### Multiple Special Directories

Pros:

- Flexible layout

Cons:

- Harder discovery
- Harder upgrades

### Hidden Files Throughout Repository

Pros:

- Minimal central structure

Cons:

- Difficult maintenance

Consequences:

Positive:

- Easier tooling
- Consistent structure
- Easier onboarding

Negative:

- Large projects may accumulate many files beneath .ot

## Amendments (As-Built)

- **Canonical Default Paths & Configurable Overrides (`src/ot/config.py`, `src/ot/scanner.py`, `src/ot/templates.py`, `src/ot/validation.py`)**:
  - `.ot/` is the canonical project root marker and fixed location for `bin/`, `config.json`, and `config.local.json`.
  - Content directories default to `.ot/tasks`, `.ot/meetings`, and `.ot/templates` and may be relocated anywhere within the project root via protected `paths.{tasks,meetings,templates}` keys in `.ot/config.json` (task `97aa42`, ADR-0036).


