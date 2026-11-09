---
id: a9baacd2-f5f4-43fa-b353-114f93722038
title: Implement ot meeting CLI subcommands (start, end, list)
type: feature
status: planned
size: medium
created_at: 2026-11-09T17:55:12.934402+00:00
updated_at: 2026-11-09T19:32:00.000000+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Implement ot meeting CLI subcommands (start, end, list)

## Overview
Implement `ot meeting start`, `ot meeting end`, and `ot meeting list` storing each meeting at `.ot/meetings/<type>/<YYYY-MM-DDTHH-MM-SS>/index.md` (with optional `attachments/` subfolder) and tracking `status: active|ended`, `started_at`, `ended_at`, `organizer`, and `attendees` in YAML frontmatter per ADR-0034.

## Acceptance Criteria
- [ ] Update default meeting templates in `src/ot/templates.py` to include `id`, `type`, `status: active`, `started_at`, `organizer`, and `attendees` in YAML frontmatter.
- [ ] `ot meeting start [--type/-t <type>] [--attendee <person>] [--edit | --no-edit]`:
  - Validate `<type>` against configured `meeting.types` (defaulting to `grooming` or requiring `--type`).
  - Render `.ot/templates/meetings/<type>.md` and write `.ot/meetings/<type>/<YYYY-MM-DDTHH-MM-SS>/index.md`.
  - Open the user's configured editor by default unless `--no-edit` is specified.
- [ ] `ot meeting end [<id_or_type>]`:
  - Locate active meetings (`status: active`) under the meetings directory.
  - Allow multiple active meetings across different types; if only one meeting is active (or unambiguous by `<id_or_type>`), set `status: ended` and `ended_at: <now_iso()>`, save `index.md`, and print a reminder to review and publish changes via pull request (ADR-0021); if multiple active meetings match, report the ambiguity and ask the user to specify the meeting ID or type.
- [ ] `ot meeting list [--status <active|ended>] [--type <type>] [--json]`:
  - List meetings in a summary table (ID, Type, Status, Started, Ended) or JSON output.
- [ ] Validate meetings in `ot check` (valid configured meeting `type`, valid `status`, valid timestamps).
- [ ] Add unit tests for `meeting start`, `meeting end`, `meeting list`, and meeting validation.

