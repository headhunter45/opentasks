---
id: 46cc7b00-a0a6-49b9-b997-4a17d0a254f5
title: Expand WorkItem, relationship cycle, link, and filesystem validation in ot check
type: feature
status: planned
size: medium
created_at: 2026-11-09T18:36:42.469806+00:00
updated_at: 2026-11-09T19:32:00.000000+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Expand WorkItem, relationship cycle, link, and filesystem validation in ot check

## Overview
Extend `ot check` and `ot check --fix` to detect parent and dependency cycles, validate relative Markdown links within the project root without network requests for external HTTP(S) URLs, and detect/repair file-vs-directory conflicts (`SomeTask.md` -> `SomeTask/index.md`) per ADR-0023 and ADR-0033.

## Acceptance Criteria
- [ ] Detect circular parent chains (`A -> B -> A`) and circular dependency chains (`A depends on B depends on A`) in `Validator.validate_work_items()`, reporting `ERROR` diagnostics.
- [ ] Detect standalone `.md` files in the tasks directory (e.g., `.ot/tasks/SomeTask.md`): if `SomeTask/index.md` already exists, emit a non-fixable `ERROR`; if `SomeTask/index.md` does not exist, emit a fixable `WARNING` and have `ot check --fix` move `SomeTask.md` -> `SomeTask/index.md`.
- [ ] Validate relative Markdown links (`[label](relative/path)` and `![alt](relative/path)`) in WorkItem and Meeting Markdown bodies/comments: verify the target file exists within `project_root` (ignoring `#anchor` fragments and skipping `http://`, `https://`, `mailto:` URLs without network calls).
- [ ] Add unit tests for parent cycles, dependency cycles, relative link validation, and `SomeTask.md` -> `SomeTask/index.md` repair.

