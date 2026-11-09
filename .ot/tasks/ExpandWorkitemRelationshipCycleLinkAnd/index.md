---
id: 46cc7b00-a0a6-49b9-b997-4a17d0a254f5
title: Expand WorkItem, relationship cycle, link, and filesystem validation in ot check
type: feature
status: triage
size: medium
created_at: 2026-11-09T18:36:42.469806+00:00
updated_at: 2026-11-09T19:06:29.672070+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Expand WorkItem, relationship cycle, link, and filesystem validation in ot check

## Overview
Extend ot check and ot check --fix to detect parent and dependency cycles, validate relative Markdown links within the project root without network requests for external HTTP(S) URLs, and detect/repair file-vs-directory conflicts (SomeTask.md -> SomeTask/index.md) per ADR-0023 and ADR-0033.
