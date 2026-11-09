---
id: d2c34f09-25bb-46bd-a761-75cb6110380b
title: JSON Schema Export
type: feature
status: completed
size: small
created_at: 2026-10-02T21:30:46.234889+00:00
updated_at: 2026-11-09T21:38:47.153336+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# JSON Schema Export

## Overview
Generate and validate Open Tasks JSON Schema definitions

## Comments

### Comment by Tom Hicks <headhunter3@gmail.com> on 2026-11-09T21:38:43.581067+00:00
<!-- comment-id: 61fe00b7-0b28-4efb-b150-d5f2e61d093c -->

Implemented JSON Schema Draft 2020-12 generation in src/ot/schema.py and CLI export via ot schema [all|config|work-item|meeting] [--output <path>] and ot config schema, with unit tests and documentation updates.
