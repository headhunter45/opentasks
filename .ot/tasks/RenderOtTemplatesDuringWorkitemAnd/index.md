---
id: 37923d1f-f38f-4879-9ae8-e2f4917bc0fe
title: Render .ot/templates/ during WorkItem and comment creation
type: feature
status: completed
size: small
created_at: 2026-11-09T17:55:09.706019+00:00
updated_at: 2026-11-09T20:35:34.176073+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Render .ot/templates/ during WorkItem and comment creation

## Overview
Update `cmd_task_create` and comment generation to load and render project templates from `.ot/templates/tasks/<type>.md` (falling back to `tasks/default.md`) and `.ot/templates/shared/comment.md` via `get_template()` as specified in ADR-0014 and ADR-0022.

## Acceptance Criteria
- [ ] Add a `render_template(template_text, context)` helper in `src/ot/templates.py` that substitutes `{{variable}}` placeholders (`id`, `title`, `type`, `status`, `size`, `created_at`, `author_name`, `author_email`, `comment_id`, `timestamp`, `body`).
- [ ] In `cmd_task_create`, load `.ot/templates/tasks/<type>.md` (or `tasks/default.md` if no type-specific template exists), render it with the new WorkItem's metadata, parse the rendered content into a `WorkItem`, and apply `--overview` / `--parent` overrides if provided.
- [ ] In `cmd_task_comment` / `Comment.to_markdown`, support rendering `.ot/templates/shared/comment.md` when available while preserving `<!-- comment-id: <id> -->` round-trip parsing.
- [ ] Add unit tests verifying that customizing `.ot/templates/tasks/bug.md` and `.ot/templates/shared/comment.md` changes the generated WorkItem and comment output.

## Comments

### Comment by Tom Hicks <headhunter3@gmail.com> on 2026-11-09T20:35:33.567355+00:00
<!-- comment-id: 04357451-974a-499a-8bf9-c18bf3fdab5b -->

Implemented render_template() in src/ot/templates.py and wired cmd_task_create and Comment.to_markdown to render .ot/templates/tasks/<type>.md and .ot/templates/shared/comment.md.
