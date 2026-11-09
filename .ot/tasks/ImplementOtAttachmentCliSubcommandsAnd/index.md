---
id: ba1cd238-5a2b-4dcd-b1a7-8e31b49eff2c
title: Implement ot attachment CLI subcommands and attachment validation
type: feature
status: triage
size: medium
created_at: 2026-11-09T18:37:01.758073+00:00
updated_at: 2026-11-09T19:06:27.661740+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Implement ot attachment CLI subcommands and attachment validation

## Overview
Implement ot attachment add, remove, list, and show subcommands storing files in <OwnerDir>/attachments/<file> referenced via relative Markdown links (no UUID/sidecar metadata), and validate relative links and warn on orphaned attachments in ot check per ADR-0033.
