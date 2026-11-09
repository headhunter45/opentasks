---
id: 36f1e10b-f6b1-408e-9377-cc2ca391140d
title: Validate edited WorkItem before saving in ot task edit and ot task create
type: feature
status: planned
size: small
created_at: 2026-11-09T18:36:45.184117+00:00
updated_at: 2026-11-09T19:32:00.000000+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Validate edited WorkItem before saving in ot task edit and ot task create

## Overview
Validate modified frontmatter and relationships when saving interactive edits in `ot task edit` and `ot task create --edit` so invalid edits are caught before overwriting the canonical file per ADR-0024 and `06-cli-reference.md`.

## Acceptance Criteria
- [ ] After the editor closes in `cmd_task_edit` and interactive `cmd_task_create`, validate the parsed `WorkItem` (valid UUID, valid configured `type`, valid configured `status`, valid configured `size` if present, no self-dependency, and valid `parent`/`dependencies` references).
- [ ] If validation fails, print clear error diagnostics to `stderr`, preserve the edited temporary file on disk (reporting its path so the user does not lose their edits), do not overwrite the canonical WorkItem file, and return exit code `1`.
- [ ] If validation succeeds, remove the temporary file and atomically write the canonical WorkItem file.
- [ ] Add unit tests covering valid interactive edits and rejected invalid edits (verifying the temp file is preserved and the original file is untouched).

