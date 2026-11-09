---
id: 7b02b1bf-ed7d-4254-9818-b7e0c2a41ae6
title: Add .ot/bin/ to .gitignore during ot init
type: bug
status: planned
size: small
created_at: 2026-11-09T04:23:01.146554+00:00
parent: 29a5aa6d-eaac-4feb-bf1d-015003fd679b
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Add .ot/bin/ to .gitignore during ot init

## Overview
Ensure ot init adds .ot/bin/ to the project's .gitignore (creating .gitignore if needed or appending idempotently) so downloaded project binaries and manifests are not tracked in source control.
