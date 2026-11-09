---
id: 143b5ec1-3947-43b6-bd02-fb2c206e2176
title: Enforce DVCS safety model pre-write checks and expand merge conflict validation
type: feature
status: triage
size: medium
created_at: 2026-11-09T17:55:06.739402+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Enforce DVCS safety model pre-write checks and expand merge conflict validation

## Overview
Implement ADR-0006 DVCS safety checks to block mutating CLI operations when the repository is in an unsafe VCS state (merge, rebase, cherry-pick, active lock) and extend ot check merge conflict marker detection to config, meeting, and template files.
