---
id: 2f1455a9-64f9-473b-8c78-651a328f2ef1
title: Make `ot task create "Fix Something"` do the same as `ot task create -m "Fix Something"`
type: feature
status: planned
size: small
created_at: 2026-10-22T01:43:19.079318+00:00
updated_at: 2026-11-09T07:31:00+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Make `ot task create "Fix Something"` do the same as `ot task create -m "Fix Something"`

## Overview
Support an optional positional `title` argument in `ot task create [title]` so that `ot task create "Fix Something"` behaves identically to `ot task create -m "Fix Something"` (and `--title` / `-m` takes precedence if both are provided).

## Acceptance Criteria
- `ot task create "Fix Something"` creates a WorkItem with title `"Fix Something"` without requiring `-m` / `--title`.
- `ot task create -m "Fix Something"` continues to work identically.
- Unit tests cover positional title creation in `tests/`.
