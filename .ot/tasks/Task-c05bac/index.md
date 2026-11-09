---
id: c05bac53-fd64-4a79-b77c-a5238b299133
title: Add task id to `ot task list` as the unnamed parameter.
type: feature
status: planned
size: small
created_at: 2026-10-22T01:26:04.356768+00:00
updated_at: 2026-11-09T07:31:00+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Add task id to `ot task list` as the unnamed parameter.

## Overview
`ot task list` should accept optional positional task IDs (both space-separated and comma-separated):
`ot task list c05bac,d05cbd`
`ot task list c05bac d05cbd`

## Acceptance Criteria
- Returns tasks matching any of the positional IDs (prefix or full UUID match).
- If any requested task IDs are unmatched, lists the ones that do match and ends with an error message on stderr naming the IDs that do not exist, returning a non-zero exit code.
- If `--json` is specified, includes the unmatched IDs in the JSON output marked as non-existing (`{"id": "<id>", "exists": false}`), and still returns a non-zero exit code.
