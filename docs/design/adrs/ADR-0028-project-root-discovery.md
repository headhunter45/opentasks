# ADR-0028 - Project Root Discovery

Status:
Accepted

Context:

OT commands may be executed from any directory inside a project.

The system requires a consistent method of locating the project root.

Decision:

OT shall discover project roots by traversing parent directories.

Recognition priority:

1. .ot
2. .git
3. .hg
4. Current working directory

Reasoning:

The project root should be discovered automatically whenever possible.

OT-specific data provides the strongest indication of an OT project.

Alternatives Considered:

### Explicit Project Root Only

Pros:

- Simple implementation

Cons:

- Poor user experience

### Git Root Only

Pros:

- Simple Git integration

Cons:

- Excludes non-Git projects

Consequences:

Positive:

- Consistent behavior
- Reduced configuration burden
- Supports DVCS and non-DVCS projects

Negative:

- Additional filesystem traversal

## Amendments (As-Built)

- **Explicit Overrides Before Traversal (`src/ot/discovery.py`, `src/ot/launcher.py`, `src/ot/cli.py`)**:
  - The CLI and global launcher support `-C <path>` / `--project-dir <path>` as the highest-priority starting directory override.
  - `find_project_root` also checks the `OPEN_TASKS_ROOT` and `OT_ROOT` environment variables before upward directory traversal.
- **Strict vs. Fallback Discovery**:
  - Existing project commands use `find_project_root()`, which strictly requires an existing `.ot/` directory in the target or an ancestor directory.
  - `discover_root()` implements the full 4-tier fallback chain (`.ot` -> `.git` -> `.hg` -> current working directory) for initialization and bootstrap workflows before `.ot/` has been created.

