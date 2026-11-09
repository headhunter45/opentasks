# ADR-0024 - Markdown First Editing Workflow

Status:
Accepted

Context:

Some project data is structured.

Some project data is narrative.

Users must be able to edit both.

Decision:

The primary editing experience shall be Markdown editing.

OT may provide convenience commands, but generated content must remain understandable and editable in standard text editors.

Reasoning:

The repository should remain usable without OT.

Markdown files should remain meaningful even when viewed directly in GitHub, GitLab, Obsidian, or a text editor.

Alternatives Considered:

### Structured Forms Only

Pros:

- Easier validation

Cons:

- Reduced transparency
- Requires OT for editing

### Database Editing

Pros:

- Strong data integrity

Cons:

- Incompatible with repository-native design

Consequences:

Positive:

- Tool independence
- Long-term portability
- Easier review

Negative:

- Parsing complexity
- Validation requirements

## Amendments (As-Built)

- **Interactive and Non-Interactive CLI Editing (`src/ot/cli.py`)**:
  - `ot task edit <id>` writes a rendered copy of the WorkItem to a temporary `.md` file, opens the user's configured editor, parses the edited Markdown and YAML frontmatter on save, updates `updated_at`, and atomically writes the canonical file.
  - `ot task create` supports both interactive editing (`--edit` or when no title is provided) and non-interactive flag-driven creation (`ot task create "Title" --no-edit`).
  - `ot task update <id>` was added (task `efd404`) to allow non-interactive updates to frontmatter fields (`--title`, `--type`, `--status`, `--size`, `--parent`, `--tag`) and the `## Overview` section (`--overview`) from scripts and AI agents while preserving the rest of the Markdown body and comments.
- **Deferred / Partial Scope**:
  - Pre-save validation of interactive edits in `ot task edit` and `ot task create --edit` before committing changes to disk is tracked in task `36f1e1`.

