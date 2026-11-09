---
id: dd264920-c0fd-4f4a-96d1-041449fa7239
title: Make the default output width configurable.
type: feature
status: planned
size: small
created_at: 2026-10-22T01:49:15.274245+00:00
updated_at: 2026-11-09T07:31:00+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Make the default output width configurable.

## Overview
Make the default table/CLI output width `120` columns. If the terminal/shell width is interactive and wider than `120` (or piped to `less` with terminal columns available), use the full available width. If the detected width is less than `120`, use `80` columns. Add a `--width` CLI parameter (and optional config setting) to override the output width. Do not affect `--json` output.

## Acceptance Criteria
- Default output width is `120` columns when non-interactive or when terminal width is `120`.
- Uses full terminal width when interactive and `> 120` columns; uses `80` columns when `< 120` columns.
- `--width <cols>` overrides the width for `ot task list` (and table formatting).
- `--json` output is unaffected by width formatting.
