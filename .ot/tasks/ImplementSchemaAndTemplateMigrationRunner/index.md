---
id: e04754c2-bd31-4556-aacd-9914d86b5808
title: Implement schema and template migration runner during ot upgrade
type: feature
status: triage
size: medium
created_at: 2026-11-09T18:37:04.573966+00:00
updated_at: 2026-11-09T19:06:28.711923+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Implement schema and template migration runner during ot upgrade

## Overview
Support checksum-aware non-destructive template upgrades (auto-update untouched default templates, preserve modified templates and write .default) and sequential single-integer system.configSchemaVersion migration steps in perform_transactional_upgrade per ADR-0035.
