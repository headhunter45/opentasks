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

- **Current Implementation**:
  - `src/ot/parser.py` (`write_work_item`) writes work item changes atomically via a temporary file in the target directory followed by `os.replace`.
  - `src/ot/validation.py` (`Validator.validate_work_items`) detects unresolved Git/VCS merge conflict markers (`<<<<<<<` and `>>>>>>>`) in work item files during `ot check`.
- **Deferred / Partial Scope**:
  - Pre-write repository state inspection (blocking mutating CLI commands when `.git/MERGE_HEAD`, `rebase-merge`, `rebase-apply`, `CHERRY_PICK_HEAD`, or lock files are present, and extending merge conflict marker checks to configuration, meeting, and template files) is not yet enforced before write operations and is tracked in task `143b5e`.

