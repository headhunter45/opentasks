---
id: efd40416-8eed-452a-947b-42f848a1736a
title: Add `ot task update <id>` subcommand to update frontmatter fields via CLI flags
type: feature
status: planned
size: small
created_at: 2026-10-22T01:42:16.356968+00:00
updated_at: 2026-11-09T07:31:00+00:00
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
