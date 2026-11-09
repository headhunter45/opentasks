---
id: 97aa42e8-aa75-4f08-82c7-60ab07d3c74f
title: Support configurable directory layout overrides in .ot/config.json
type: feature
status: planned
size: small
created_at: 2026-11-09T18:36:33.816969+00:00
updated_at: 2026-11-09T19:32:00.000000+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Support configurable directory layout overrides in .ot/config.json

## Overview
Support relocating `tasks`, `meetings`, and `templates` directories anywhere within the project root (parent of `.ot`) via protected `paths.{tasks,meetings,templates}` keys in `.ot/config.json` while keeping `.ot/bin` and `.ot/config*.json` fixed per ADR-0036.

## Acceptance Criteria
- [ ] Add `paths` (`paths.tasks`, `paths.meetings`, `paths.templates`) to `DEFAULT_CONFIG` (defaulting to `.ot/tasks`, `.ot/meetings`, `.ot/templates`) and `PROTECTED_CONFIG_KEYS` in `src/ot/config.py`, with helper properties `config.tasks_dir`, `config.meetings_dir`, and `config.templates_dir`.
- [ ] Enforce containment validation: any configured path that resolves outside `project_root` (e.g., `../outside` or external absolute paths) raises a configuration validation `ERROR` in `ot check`.
- [ ] Update `RepositoryScanner`, `templates.py`, `cli.py`, and `validation.py` to resolve `tasks`, `meetings`, and `templates` directories via `Config`.
- [ ] When a path is reconfigured, create the new directory if needed (or via `ot check --fix`) without automatically moving files, and emit a `WARNING` in `ot check` if the non-default old `.ot/<subdir>` still contains files so the user can move them explicitly (e.g. with `git mv`).
- [ ] Add unit tests for custom `paths` (such as `docs/tasks` and `docs/meetings`), path traversal rejection, and leftover-file warnings.

