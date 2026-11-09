---
id: 30dc4752-1ff9-4939-b66a-29b3e637f5c2
title: Implement ot config CLI subcommands (get, set, list)
type: feature
status: planned
size: medium
created_at: 2026-11-09T18:36:36.770170+00:00
updated_at: 2026-11-09T19:32:00.000000+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Implement ot config CLI subcommands (get, set, list)

## Overview
Implement configuration inspection and modification commands (`ot config get`, `ot config set`, `ot config list --show-origin`) to inspect resolved values across layers and write settings to local, project, or global config per ADR-0011, ADR-0012, ADR-0013, and ADR-0016.

## Acceptance Criteria
- [ ] `ot config get <key>`: Print the resolved configuration value for a dot-notation key (e.g., `user.editor`, `workItem.types.bug.label`), with optional `--show-origin` showing which layer supplied the value (`.ot/config.local.json`, `.ot/config.json`, `~/.ot/config.json`, VCS, environment, or default).
- [ ] `ot config set <key> <value> [--local | --project | --global]`:
  - When no layer flag is passed, auto-select the target file based on the key: write protected keys (`PROTECTED_CONFIG_KEYS` or subkeys) to `.ot/config.json` and non-protected user keys to `.ot/config.local.json`.
  - Support `--local`, `--project`, and `--global` flags to explicitly target `.ot/config.local.json`, `.ot/config.json`, or `~/.ot/config.json`, emitting a warning to `stderr` if `--local` or `--global` is forced on a protected key.
  - Parse JSON literals (`true`, `false`, numbers, JSON objects/arrays) or store strings cleanly.
- [ ] `ot config list [--show-origin] [--json]`: Display all resolved configuration keys and values, optionally annotated with their origin layer.
- [ ] Add unit tests for `get`, `set` (auto-routing + explicit flags + protected key warning), and `list --show-origin`.

