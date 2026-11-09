---
id: 143b5ec1-3947-43b6-bd02-fb2c206e2176
title: Enforce DVCS safety model pre-write checks and expand merge conflict validation
type: feature
status: completed
size: medium
created_at: 2026-11-09T17:55:06.739402+00:00
updated_at: 2026-11-09T21:12:27.927120+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Enforce DVCS safety model pre-write checks and expand merge conflict validation

## Overview
Implement ADR-0006 DVCS safety checks to block mutating CLI operations when the repository is in an unsafe VCS state (merge, rebase, cherry-pick, active lock) and extend `ot check` merge conflict marker detection to config, meeting, and template files.

## Acceptance Criteria
- [ ] Add `check_vcs_safety(project_root)` in `src/ot/discovery.py` detecting unsafe Git states (`.git/MERGE_HEAD`, `.git/rebase-merge`, `.git/rebase-apply`, `.git/CHERRY_PICK_HEAD`, `.git/REVERT_HEAD`, `.git/BISECT_LOG`, `.git/index.lock`) and Mercurial states (`.hg/merge/`, `.hg/rebasestate`, `.hg/histedit-state`, `.hg/wlock`).
- [ ] Refuse mutating CLI commands (`init`, `upgrade`, `check --fix`, `task create/edit/update/status/comment/add-dependency/remove-dependency`, `meeting start/end`, `attachment add/remove`, `config set`) with exit code `1` and an actionable error message when the repository is in an unsafe VCS state, unless `--force` is passed.
- [ ] Permit read-only commands (`task list`, `task show`, `task get-dependencies`, `check`, `version`, `config get/list`, `meeting list`, `attachment list/show`) during unsafe VCS states.
- [ ] Extend `Validator` in `src/ot/validation.py` to report a `vcs` diagnostic when in an unsafe VCS state and scan `.ot/config.json`, `.ot/config.local.json`, templates, and meetings for unresolved Git/Hg conflict marker lines.
- [ ] Add unit tests for Git/Hg unsafe states, `--force` bypass, and conflict marker detection across config/templates/meetings.

## Comments

### Comment by Tom Hicks <headhunter3@gmail.com> on 2026-11-09T21:12:27.446285+00:00
<!-- comment-id: 0cce52ce-2bbb-43c6-a8bc-348ebacc7549 -->

Added check_vcs_safety for Git and Mercurial, enforced pre-write DVCS safety checks across mutating CLI commands (with --force bypass), and expanded conflict marker validation to config, templates, and meetings.
