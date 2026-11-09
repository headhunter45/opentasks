# ADR-0003 - Unified WorkItem Model

Status:
Accepted

Context:

OT originally distinguished between Tasks and Epics.

As planning requirements expanded, users needed:

- Nested epics
- Feature groups
- Releases
- Subtasks
- Decomposition of large tasks

Maintaining separate Task and Epic models created duplicated behavior and artificial constraints.

Decision:

Use a single WorkItem model.

Work items may contain child work items.

Examples include:

- Release work items
- Epic work items
- Task work items
- Bug work items
- Enhancement work items
- Spike work items
- Chore work items

Type becomes metadata rather than implementation.

Reasoning:

Planning artifacts primarily differ by purpose rather than structure.

A unified model simplifies:

- Storage
- Validation
- Relationships
- CLI commands
- Reporting

Alternatives Considered:

### Separate Epic and Task Models

Pros:

- Familiar to Jira users
- Distinct validation paths

Cons:

- Duplicated code
- Artificial hierarchy
- Difficult nesting

### Fixed Hierarchy

Release → Epic → Task

Pros:

- Clear structure

Cons:

- Restrictive
- Difficult to evolve
- Not suitable for all teams

Consequences:

Positive:

- Unlimited nesting
- Simpler implementation
- Consistent relationships
- Flexible planning structures

Negative:

- Requires conventions to distinguish intent
- Some reports may require additional filtering

## Amendments (As-Built)

- **Default Configured WorkItem Types**: In `src/ot/config.py` (`DEFAULT_CONFIG`) and `src/ot/templates.py` (`DEFAULT_TEMPLATES`), the default configured types installed on project initialization are `task`, `bug`, `feature`, `epic`, `spike`, and `chore` (`feature` is used in place of `enhancement`, and `release` is not pre-configured by default, though projects may add custom types in `.ot/config.json`).
- **CLI Subcommand Naming**: For familiarity and brevity, the CLI groups WorkItem operations under `ot task <command>` (`list`, `show`, `create`, `edit`, `update`, `status`, `comment`, `add-dependency`, `remove-dependency`, `get-dependencies`) while operating uniformly across all WorkItem types.

``
