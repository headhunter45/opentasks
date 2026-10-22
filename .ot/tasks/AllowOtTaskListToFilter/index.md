---
id: 229d60f7-d0ed-40a0-a917-b6ab030f3c61
title: Allow `ot task list` to filter by more frontmatter values.
type: task
status: triage
created_at: 2026-10-22T01:56:12.274345+00:00
updated_at: 2026-10-22T02:01:24.036797+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Allow `ot task list` to filter by more frontmatter values.

## Overview

all of these need to be treated like --status with their own flag to search

id: Match values if they match starts with or equals the value
title: Match values if they match starts with or equals the value
type: Match values if they match starts with or equals the value. If a value does not match then error and list the allowed types.
status: Match values if they match starts with or equals the value. If a value does not match then error and list the allowed types.
author: Match values against name and/or email as a regex if it begins with `/` and ends with `/` otherwise treat it as a value is anywher in the string.
