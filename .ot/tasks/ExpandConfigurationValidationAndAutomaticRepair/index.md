---
id: a9c5dee2-1e5b-47dd-b2ab-639db6950950
title: Expand configuration validation and automatic repair in ot check
type: feature
status: planned
size: small
created_at: 2026-11-09T18:36:39.497473+00:00
updated_at: 2026-11-09T19:32:00.000000+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Expand configuration validation and automatic repair in ot check

## Overview
Extend `Validator.validate_configuration` and `Repairer.repair` to validate `~/.ot/config.json`, check `configSchemaVersion` compatibility across layers, warn on protected keys in global user config, and support fine-grained dotted protected key repair per ADR-0016 and ADR-0017.

## Acceptance Criteria
- [ ] Validate JSON syntax and `system.configSchemaVersion` compatibility across `.ot/config.json`, `.ot/config.local.json`, and `~/.ot/config.json` (or `$OT_USER_HOME/config.json`).
- [ ] Emit `WARNING` diagnostics when `PROTECTED_CONFIG_KEYS` are present in `.ot/config.local.json` or `~/.ot/config.json`.
- [ ] Enhance `Repairer.repair` (`ot check --fix`) to deep-merge and relocate individual protected keys (e.g. `workItem.statuses`, `project.name`) from `.ot/config.local.json` to `.ot/config.json` and clean up empty parent dicts in `config.local.json`.
- [ ] Add unit tests covering cross-layer schema version mismatches, global config validation, and fine-grained protected key repair.

