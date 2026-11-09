---
id: ba1cd238-5a2b-4dcd-b1a7-8e31b49eff2c
title: Implement ot attachment CLI subcommands and attachment validation
type: feature
status: completed
size: medium
created_at: 2026-11-09T18:37:01.758073+00:00
updated_at: 2026-11-09T21:31:58.669071+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Implement ot attachment CLI subcommands and attachment validation

## Overview
Implement `ot attachment add`, `remove`, `list`, and `show` subcommands storing files in `<OwnerDir>/attachments/<file>` referenced via relative Markdown links (no UUID/sidecar metadata), and validate relative links and warn on orphaned attachments in `ot check` per ADR-0033.

## Acceptance Criteria
- [ ] `ot attachment add <item_or_meeting_id> <file_path> [--label <text>]`:
  - Copy `<file_path>` into `<OwnerDir>/attachments/<filename>` (creating `attachments/` if needed).
  - Append a relative Markdown link to the owner's `index.md` body (`![<label>](attachments/<filename>)` for image extensions `.png/.jpg/.jpeg/.gif/.svg/.webp`, or `[<label>](attachments/<filename>)` for other files).
- [ ] `ot attachment remove <item_or_meeting_id> <filename>`:
  - Delete `<OwnerDir>/attachments/<filename>` and remove its Markdown link reference from `index.md`.
- [ ] `ot attachment list <item_or_meeting_id> [--json]`:
  - List all attachment files and Markdown references for the given WorkItem or Meeting.
- [ ] `ot attachment show <item_or_meeting_id> <filename>`:
  - Display the resolved path, file size, existence status, and referencing lines in `index.md`.
- [ ] In `ot check`, warn (`Severity.WARNING`) on orphaned files inside `<OwnerDir>/attachments/` that are not referenced anywhere in `index.md` (without deleting them in `--fix`), and report an `ERROR` if an `attachments/<file>` link points to a missing file.
- [ ] Add unit tests for `attachment add`, `remove`, `list`, `show`, and orphan/broken-link validation.

## Comments

### Comment by Tom Hicks <headhunter3@gmail.com> on 2026-11-09T21:31:56.558579+00:00
<!-- comment-id: 2633a864-d398-4833-a21d-1dddd78a0867 -->

Implemented ot attachment CLI subcommands (add, remove, list, show), orphaned attachment WARNING detection and broken attachment link ERROR validation in Validator, updated ADR-0033 and 06-cli-reference.md, and added unit tests.
