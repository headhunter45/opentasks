---
id: dd264920-c0fd-4f4a-96d1-041449fa7239
title: Make the default output width configurable.
type: task
status: triage
created_at: 2026-10-22T01:49:15.274245+00:00
updated_at: 2026-10-22T01:50:18.733240+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

Make the default output width 120 cols. If the terminal/shell width is interactive and wider or something like piping to less then use all of the available width. If the width is less than 120 make the default width 80. Add a --width parameter somewhere to specify an override for this too. This should not affect json output.


## Overview
