---
id: e04754c2-bd31-4556-aacd-9914d86b5808
title: Implement schema and template migration runner during ot upgrade
type: feature
status: completed
size: medium
created_at: 2026-11-09T18:37:04.573966+00:00
updated_at: 2026-11-09T21:04:14.712686+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Implement schema and template migration runner during ot upgrade

## Overview
Support checksum-aware non-destructive template upgrades (auto-update untouched default templates, preserve modified templates and write `.default`) and sequential single-integer `system.configSchemaVersion` migration steps in `perform_transactional_upgrade` per ADR-0035.

## Acceptance Criteria
- [ ] Maintain a registry of known built-in template SHA-256 digests (`KNOWN_DEFAULT_TEMPLATE_HASHES`) in `src/ot/templates.py`.
- [ ] Update template installation during `ot upgrade`:
  - Install any missing default template files.
  - If an existing template file matches a known built-in default hash and differs from the current release's default template, update it in place.
  - If an existing template file was modified by the user and differs from the current release's default template, preserve the user's file untouched and write the new default template to `<template>.default`, reporting a notice in the upgrade result.
- [ ] Add a sequential configuration schema migration runner (`run_config_migrations(config_data, target_schema_version)`) in `src/ot/upgrade.py` that applies registered `v -> v+1` migration functions in staging during `perform_transactional_upgrade` for both `config.json` and `config.local.json`.
- [ ] Add unit tests for untouched template auto-updates, user-modified template preservation (`.default` creation), and sequential config schema migrations in transactional upgrades.

## Comments

### Comment by Tom Hicks <headhunter3@gmail.com> on 2026-11-09T21:04:12.515147+00:00
<!-- comment-id: fd235d70-4100-4de6-8cec-0ed4bda9688c -->

Implemented checksum-aware non-destructive template upgrades (upgrade_project_templates) and sequential config schema migrations (run_config_migrations) during ot upgrade.
