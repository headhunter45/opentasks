---
id: c05bac53-fd64-4a79-b77c-a5238b299133
title: Add task id to `ot task list` as the unnamed parameter.
type: task
status: triage
created_at: 2026-10-22T01:26:04.356768+00:00
updated_at: 2026-10-22T01:38:14.869766+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

These should return the tasks with either of these ids. If the parameters match an actual subcommand that should take priority. If any of the task ids are unmatched we should list the ones that do match and end with an error message that those ids don't exist. If --json is specified we can include the missed tasks in the json output as non-existing, but we should still return an error status code from the command.
`ot task list c05bac,d05cbd`
`ot task list c05bac d05cbd`
