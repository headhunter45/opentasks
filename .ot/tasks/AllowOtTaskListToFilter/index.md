---
id: 229d60f7-d0ed-40a0-a917-b6ab030f3c61
title: Allow `ot task list` to filter by more frontmatter values.
type: feature
status: completed
size: medium
created_at: 2026-10-22T01:56:12.274345+00:00
updated_at: 2026-11-09T08:02:56.713808+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
dependencies:
  - 98426040-3a5a-4f78-8232-9da6262ec6a9
---

# Allow `ot task list` to filter by more frontmatter values.

## Overview
All of these fields should be supported on `ot task list` with their own flag (supporting multi-value and comma-separated matching per `984260`):

- `--id`: Match values if they start with or equal the filter value (case-insensitive).
- `--title`: Match values if they start with or equal the filter value (case-insensitive).
- `--type` / `-t`: Match values if they start with or equal an allowed type. If a value does not match any allowed type, print an error listing the allowed types and exit non-zero.
- `--status` / `-s`: Match values if they start with or equal an allowed status. If a value does not match any allowed status, print an error listing the allowed statuses and exit non-zero.
- `--author`: Match values against `author.name` and/or `author.email` as a regex if the filter value begins with `/` and ends with `/`; otherwise match if the value appears anywhere in `name` or `email` (case-insensitive).

## Comments

### Comment by Tom Hicks <headhunter3@gmail.com> on 2026-11-09T08:02:56.344617+00:00
<!-- comment-id: dea6b25d-87a9-4f0b-970e-6a35e54f023e -->

Implementation notes: Added --id and --title prefix filters, --type and --status allowed-value validation with non-zero exit codes, and --author substring and /regex/ matching against name and email.
