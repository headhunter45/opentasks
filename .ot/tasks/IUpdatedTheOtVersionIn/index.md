---
id: 65e1942e-9fa4-4a43-b059-82d64096184d
title: I updated the ot version in config.json, but `ot task list` did not try to download the new version.
type: bug
status: closed
created_at: 2026-10-22T02:17:50.866712+00:00
updated_at: 2026-11-09T04:23:24.570773+00:00
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

## Comments

### Comment by Tom Hicks <headhunter3@gmail.com> on 2026-11-09T04:23:24.217369+00:00
<!-- comment-id: 15db36b7-89ef-4256-9bc8-9653dd9506ac -->

Triaged and split into planned tasks under 29a5aa: 7b02b1 (.gitignore on ot init), 7339ca (zipapp launcher delegation), and 29ed8a (versioned .ot/bin/<version>/ storage and auto-download). Note: the ot init source package failure when running from a distributed zipapp was fixed in commit aeb1acc.
