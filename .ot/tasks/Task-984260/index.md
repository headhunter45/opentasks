---
id: 98426040-3a5a-4f78-8232-9da6262ec6a9
title: Allow searching by multiple columns and column values.
type: feature
status: planned
size: medium
created_at: 2026-10-22T01:25:52.819774+00:00
updated_at: 2026-11-09T07:31:00+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Allow searching by multiple columns and column values.

## Overview
Commands like these should select all tasks that match any of the values.
Both of these should return all tasks that are in any of the three statuses:
`ot task list -s triage -s in_progress -s planned`
`ot task list -s triage,in_progress,planned`

Specifically, AND together the different columns and OR together the different values specified per column.
This should show all tasks that are (either in `triage` OR `planned` status) AND (either of the `task` OR `chore` type):
`ot task list -s triage,planned -t task,chore`

Support prefix matching from the start of the column value:
`ot task list -s tr,lan,in` should show tasks in `triage` and `in_progress`, but not `planned`.
