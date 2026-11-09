---
id: 7339ca21-f00f-4a40-b196-aeb33f378a90
title: Route packaged ot.zipapp entry point through global launcher
type: bug
status: completed
size: small
created_at: 2026-11-09T04:23:05.064809+00:00
updated_at: 2026-11-09T04:28:34.232394+00:00
parent: 29a5aa6d-eaac-4feb-bf1d-015003fd679b
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Route packaged ot.zipapp entry point through global launcher

## Overview
Update build_zipapp_artifact in src/ot/packaging.py so __main__.py invokes ot.launcher:run_launcher instead of ot.cli:main directly, while guarding against recursive re-delegation when launching a project binary.

## Comments

### Comment by Tom Hicks <headhunter3@gmail.com> on 2026-11-09T04:28:32.452658+00:00
<!-- comment-id: 641416b1-ed6c-41d8-8362-d8407d1cda82 -->

Implementation notes: Updated build_zipapp_artifact in src/ot/packaging.py to default main_func to ot.launcher:run_launcher, added recursion guards (OT_PROJECT_BINARY_ACTIVE and _is_running_binary) and -C/--project-dir extraction in src/ot/launcher.py, and added subprocess test in tests/test_launcher.py.
