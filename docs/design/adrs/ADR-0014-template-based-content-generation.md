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
- **Rendered Content Creation (`src/ot/templates.py`, `src/ot/cli.py`, `src/ot/models.py`)**:
  - `cmd_task_create` renders `.ot/templates/tasks/<type>.md` (falling back to `tasks/default.md`) via `render_template()`, and `Comment.to_markdown` renders `.ot/templates/shared/comment.md` (`37923d`).
  - Implementing `ot meeting` CLI subcommands (`start`, `end`, `list`) using `.ot/templates/meetings/<type>.md` is tracked in task `a9baac`.

