---
id: 29ed8a03-c5e8-43cc-8196-a239e5e3f72e
title: Store project binaries in .ot/bin/<version>/ and auto-download configured version
type: bug
status: completed
size: medium
created_at: 2026-11-09T04:23:09.365580+00:00
updated_at: 2026-11-09T04:36:06.817234+00:00
parent: 29a5aa6d-eaac-4feb-bf1d-015003fd679b
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Store project binaries in .ot/bin/<version>/ and auto-download configured version

## Overview
Store and resolve project binaries at .ot/bin/<version>/ot.zipapp with .ot/bin/<version>/ot-manifest.json, preserving older versions. When system.toolVersion in .ot/config.json is missing from .ot/bin/<version>/, both ot and otw should check ~/.ot/versions/<version>/ cache first, download from GitHub Releases with SHA256SUMS verification if not cached, and install into .ot/bin/<version>/.

## Comments

### Comment by Tom Hicks <headhunter3@gmail.com> on 2026-11-09T04:36:06.423807+00:00
<!-- comment-id: eb7cd7c8-5e28-41e5-be2d-519f0e15259d -->

Implementation notes: Updated install_project_binary, perform_transactional_upgrade, discover_installed_version, find_project_binary, ensure_project_binary, and otw/WRAPPER_SCRIPT_SH to store and resolve binaries under .ot/bin/<version>/ot.zipapp with .ot/bin/<version>/ot-manifest.json while preserving older versions. Added download_version_artifact in src/ot/cache.py with SHA256SUMS verification and ~/.ot/versions/<version>/ caching.
