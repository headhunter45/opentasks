---
id: 29ed8a03-c5e8-43cc-8196-a239e5e3f72e
title: Store project binaries in .ot/bin/<version>/ and auto-download configured version
type: bug
status: planned
size: medium
created_at: 2026-11-09T04:23:09.365580+00:00
parent: 29a5aa6d-eaac-4feb-bf1d-015003fd679b
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Store project binaries in .ot/bin/<version>/ and auto-download configured version

## Overview
Store and resolve project binaries at .ot/bin/<version>/ot.zipapp with .ot/bin/<version>/ot-manifest.json, preserving older versions. When system.toolVersion in .ot/config.json is missing from .ot/bin/<version>/, both ot and otw should check ~/.ot/versions/<version>/ cache first, download from GitHub Releases with SHA256SUMS verification if not cached, and install into .ot/bin/<version>/.
