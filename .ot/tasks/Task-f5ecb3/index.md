---
id: f5ecb37f-1a89-4cfa-b102-f682f4d2903b
title: Rename the wrapper from `otw` to `oat`.
type: task
status: planned
size: medium
created_at: 2026-10-22T01:26:14.134660+00:00
updated_at: 2026-11-09T07:31:00+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Rename the wrapper from `otw` to `oat`.

## Overview
Rename the project wrapper scripts from `otw` / `otw.bat` to `oat` / `oat.bat`.

## Acceptance Criteria
- `ot init` creates `oat` and `oat.bat` instead of `otw` and `otw.bat`.
- `ot upgrade` creates/updates `oat` and `oat.bat` and removes legacy `otw` and `otw.bat` files if present.
- Repository root `otw` / `otw.bat` are replaced by `oat` / `oat.bat`.
- Skills (`.agents/skills/`) and unit tests are updated to reference `./oat`.
