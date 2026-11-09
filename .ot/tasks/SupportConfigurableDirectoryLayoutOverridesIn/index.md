---
id: 97aa42e8-aa75-4f08-82c7-60ab07d3c74f
title: Support configurable directory layout overrides in .ot/config.json
type: feature
status: triage
size: small
created_at: 2026-11-09T18:36:33.816969+00:00
updated_at: 2026-11-09T19:06:29.181263+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Support configurable directory layout overrides in .ot/config.json

## Overview
Support relocating tasks, meetings, and templates directories anywhere within the project root (parent of .ot) via protected paths.{tasks,meetings,templates} keys in .ot/config.json while keeping .ot/bin and .ot/config*.json fixed per ADR-0036.
