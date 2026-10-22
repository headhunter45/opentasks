---
id: 65e1942e-9fa4-4a43-b059-82d64096184d
title: I updated the ot version in config.json, but `ot task list` did not try to download the new version.
type: bug
status: triage
created_at: 2026-10-22T02:17:50.866712+00:00
updated_at: 2026-10-22T02:24:25.826958+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# I updated the ot version in config.json, but `ot task list` did not try to download the new version.

## Overview
The installed ot at `/Users/tom/.local/bin/ot` should be using the ot.zipapp in our .ot/bin directory. 
`.ot/bin` should have been added to .bigignore by the initial `ot init`, but was not.
`./otw task list` did not download a separate version either.
Bot ot and otw should be using the version installed in the project and specified in config.json. The downloaded versions should not be in source control. We should save old versions so each version should be downloaded to `.ot/bin/${version}/ot.zipapp` along with its manifest.
`ot init` is failing with this message as well. "Initialization failed: Source package not found at /Users/tom/.local/bin/src/ot"
