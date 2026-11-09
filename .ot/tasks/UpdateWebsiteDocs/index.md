---
id: 29ba55c6-63aa-4e18-adea-d0fc6777c735
title: Update website docs.
type: chore
status: completed
size: small
created_at: 2026-10-21T05:46:02.138506+00:00
updated_at: 2026-11-09T08:13:34.124581+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
dependencies:
  - f5ecb37f-1a89-4cfa-b102-f682f4d2903b
  - 2f1455a9-64f9-473b-8c78-651a328f2ef1
  - efd40416-8eed-452a-947b-42f848a1736a
  - dd264920-c0fd-4f4a-96d1-041449fa7239
  - 98426040-3a5a-4f78-8232-9da6262ec6a9
  - 229d60f7-d0ed-40a0-a917-b6ab030f3c61
  - c05bac53-fd64-4a79-b77c-a5238b299133
---

# Update website docs.

## Overview
Update `web/index.html`, `README.md`, and `docs/design/` to reflect the new CLI capabilities and conventions once the planned CLI and wrapper tasks are implemented:
- `oat` / `oat.bat` project wrapper scripts (replacing `otw` / `otw.bat`)
- `.ot/bin/<version>/ot.zipapp` versioned binary layout
- `ot task update <id>` subcommand
- Multi-column / multi-value / positional ID filtering in `ot task list` and positional title in `ot task create`

## Comments

### Comment by Tom Hicks <headhunter3@gmail.com> on 2026-11-09T08:13:33.729144+00:00
<!-- comment-id: 8415b107-a72f-4c3e-971f-b79b7dba9224 -->

Implementation notes: Updated web/index.html, README.md, and docs/design/ to document oat/oat.bat wrappers, .ot/bin/<version>/ot.zipapp layout, ot task update, and enhanced ot task list / ot task create options.
