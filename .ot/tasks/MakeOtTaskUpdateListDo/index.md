---
id: efd40416-8eed-452a-947b-42f848a1736a
title: Add `ot task update <id>` subcommand to update frontmatter fields via CLI flags
type: feature
status: completed
size: small
created_at: 2026-10-22T01:42:16.356968+00:00
updated_at: 2026-11-09T07:50:55.357611+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Add `ot task update <id>` subcommand to update frontmatter fields via CLI flags

## Overview
Add an `ot task update <id>` subcommand to `src/ot/cli.py` to update a WorkItem's frontmatter metadata (`--title` / `-m`, `--status` / `-s`, `--type` / `-t`, `--size`, `--parent` / `-p`, `--tag`) and overview (`--overview`) directly via CLI flags without launching an interactive editor.

## Acceptance Criteria
- `ot task update <id>` resolves the target WorkItem by ID, short ID, or title.
- Supports updating `--title`/`-m`, `--status`/`-s`, `--type`/`-t`, `--size`, `--parent`/`-p`, and `--tag`, validating configured values and updating `updated_at`.
- Removes duplicate `build_parser()` definition in `src/ot/cli.py`.
- Covered by unit tests.

## Comments

### Comment by Tom Hicks <headhunter3@gmail.com> on 2026-11-09T07:50:55.005944+00:00
<!-- comment-id: dece623a-8a52-4565-b89b-f90be9f89de1 -->

Implementation notes: Added cmd_task_update and ot task update subcommand to update title, status, type, size, parent, tag, and overview via CLI flags, and removed duplicate build_parser() in src/ot/cli.py.
