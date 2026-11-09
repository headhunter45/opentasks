---
id: 37923d1f-f38f-4879-9ae8-e2f4917bc0fe
title: Render .ot/templates/ during WorkItem and comment creation
type: feature
status: triage
size: small
created_at: 2026-11-09T17:55:09.706019+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Render .ot/templates/ during WorkItem and comment creation

## Overview
Update cmd_task_create and comment generation to load and render project templates from .ot/templates/tasks/<type>.md and .ot/templates/shared/comment.md via get_template() as specified in ADR-0014 and ADR-0022.
