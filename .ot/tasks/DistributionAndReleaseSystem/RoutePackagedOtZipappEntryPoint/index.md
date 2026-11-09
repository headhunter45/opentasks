---
id: 7339ca21-f00f-4a40-b196-aeb33f378a90
title: Route packaged ot.zipapp entry point through global launcher
type: bug
status: planned
size: small
created_at: 2026-11-09T04:23:05.064809+00:00
parent: 29a5aa6d-eaac-4feb-bf1d-015003fd679b
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Route packaged ot.zipapp entry point through global launcher

## Overview
Update build_zipapp_artifact in src/ot/packaging.py so __main__.py invokes ot.launcher:run_launcher instead of ot.cli:main directly, while guarding against recursive re-delegation when launching a project binary.
