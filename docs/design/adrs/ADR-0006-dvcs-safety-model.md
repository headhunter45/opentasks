# ADR-0006 - DVCS Safety Model

Status:
Accepted

Context:

OT modifies files that may also be modified by version control systems.

Examples include:

- Work item files
- Meeting files
- Configuration files
- Templates

Simultaneous modification by OT and a version control system can create inconsistent state or data loss.

Decision:

OT shall use a two-state safety model:

- Safe
- Unsafe

When the repository is in an unsafe state, OT shall refuse write operations.

Examples of unsafe states include:

- Merge operations
- Rebase operations
- Interactive rebases
- Cherry-picks
- Active version-control locks
- Other repository rewrite operations

Read-only operations may still be permitted.

Reasoning:

A binary safety model is easier to understand, easier to test, and easier to extend than operation-specific behavior.

Alternatives Considered:

### Operation-Specific Rules

Pros:

- More permissive

Cons:

- Difficult to reason about
- Difficult to test
- Easy to introduce edge cases

### Ignore Version Control State

Pros:

- Simplest implementation

Cons:

- Increased risk of corruption
- Race conditions
- Inconsistent results

Consequences:

Positive:

- Predictable behavior
- Reduced data corruption risk
- Simplified implementation

Negative:

- Some operations may be unnecessarily blocked
- Additional repository inspection required

## Amendments (As-Built)

- **Implemented DVCS Safety & Conflict Detection (`src/ot/discovery.py`, `src/ot/cli.py`, `src/ot/validation.py`, `src/ot/parser.py`)**:
  - `check_vcs_safety()` inspects Git (`.git/MERGE_HEAD`, `rebase-merge`, `rebase-apply`, `CHERRY_PICK_HEAD`, `REVERT_HEAD`, `BISECT_LOG`, `index.lock`) and Mercurial (`.hg/merge`, `rebasestate`, `histedit-state`, `wlock`) state before any mutating CLI command (`init`, `upgrade`, `check --fix`, `config set`, `task create/edit/update/status/comment/add-dependency/remove-dependency`, `meeting start/end`, `attachment add/remove`), blocking write operations with exit code `1` unless `--force` is passed while allowing read-only commands (`task list`, `task show`, `check`, `version`, `config get/list`, etc.) (task `143b5e`).
  - `write_work_item` writes work item changes atomically via a temporary file in the target directory followed by `os.replace`.
  - `Validator` reports active unsafe VCS states (`category="vcs"`) and scans WorkItems, `.ot/config.json`, `.ot/config.local.json`, templates, and meetings for unresolved merge conflict marker lines (`category="merge_conflict"`, `Severity.ERROR`).


