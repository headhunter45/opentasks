---
id: a9baacd2-f5f4-43fa-b353-114f93722038
title: Implement ot meeting CLI subcommands (start, end, list)
type: feature
status: triage
size: medium
created_at: 2026-11-09T17:55:12.934402+00:00
updated_at: 2026-11-09T19:06:28.191598+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Implement ot meeting CLI subcommands (start, end, list)

## Overview
Implement ot meeting start, ot meeting end, and ot meeting list storing each meeting at .ot/meetings/<type>/<YYYY-MM-DDTHH-MM-SS>/index.md (with optional attachments/ subfolder) and tracking status: active|ended, started_at, ended_at, organizer, and attendees in YAML frontmatter per ADR-0034.
