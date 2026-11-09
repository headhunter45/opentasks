# ADR-0014 - Template Based Content Generation

Status:
Accepted

Context:

Work items, meetings, comments, and attachments require consistent initial structure.

Users should also be able to customize those structures.

Decision:

OT shall generate content from templates stored within the project.

Initial template categories include:

- Work items
- Meetings
- Shared templates

Default templates are installed during initialization.

Reasoning:

Templates allow projects to customize workflows without modifying OT source code.

Alternatives Considered:

### Hardcoded Templates

Pros:

- Simpler implementation

Cons:

- Difficult customization
- Requires OT modifications

### Global Templates

Pros:

- Easy user customization

Cons:

- Inconsistent repository behavior

Consequences:

Positive:

- Project-specific customization
- Reviewable template changes
- Consistent generation

Negative:

- Template migration complexity
- Additional validation requirements

## Amendments (As-Built)

- **Installed Template Layout (`src/ot/templates.py`)**:
  - `install_default_templates` installs `tasks/{default,bug,feature,epic,spike,chore}.md`, `meetings/{grooming,planning,retrospective,ideation}.md`, and `shared/comment.md` into `.ot/templates/` using `{{variable}}` placeholders.
  - `get_template` resolves `.ot/templates/<name>` first and falls back to built-in `DEFAULT_TEMPLATES`.
- **Deferred / Partial Scope**:
  - While templates are installed and managed during `ot init` and `ot upgrade`, `cmd_task_create` (`src/ot/cli.py`) and `Comment.to_markdown` (`src/ot/models.py`) currently construct initial WorkItem bodies and comments directly in Python rather than rendering `.ot/templates/tasks/<type>.md` or `.ot/templates/shared/comment.md`, and `ot meeting` CLI subcommands are not yet implemented. Wiring content creation to render project templates and implementing meeting subcommands are tracked in tasks `37923d` and `a9baac`.

