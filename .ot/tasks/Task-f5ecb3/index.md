---
id: f5ecb37f-1a89-4cfa-b102-f682f4d2903b
title: Rename the wrapper from `otw` to `oat`.
type: task
status: completed
size: medium
created_at: 2026-10-22T01:26:14.134660+00:00
updated_at: 2026-11-09T08:10:13.083514+00:00
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

## Comments

### Comment by Tom Hicks <headhunter3@gmail.com> on 2026-11-09T08:10:12.626744+00:00
<!-- comment-id: 04a244c0-94d9-44ba-be64-531c11f33d8f -->

Implementation notes: Renamed wrapper scripts from otw/otw.bat to oat/oat.bat in init_project, perform_transactional_upgrade (removing legacy otw/otw.bat on upgrade), repo root, agent skills, and unit tests.
