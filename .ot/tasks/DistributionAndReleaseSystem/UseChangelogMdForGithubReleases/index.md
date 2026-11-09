---
id: f52a8f8d-2e40-425b-a488-b0e7fd6461cb
title: Use CHANGELOG.md for GitHub Releases and website release notes
type: feature
status: completed
size: small
created_at: 2026-11-09T06:34:02.491201+00:00
updated_at: 2026-11-09T06:49:15.613521+00:00
parent: 29a5aa6d-eaac-4feb-bf1d-015003fd679b
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Use CHANGELOG.md for GitHub Releases and website release notes

## Overview
Update .github/workflows/deploy.yml to pass CHANGELOG.md as the release notes (--notes-file CHANGELOG.md) when creating/updating a GitHub Release, and render CHANGELOG.md contents on the website (web/index.html) during site preparation.

## Comments

### Comment by Tom Hicks <headhunter3@gmail.com> on 2026-11-09T06:49:15.166729+00:00
<!-- comment-id: 54e8728f-7cd0-437f-a032-77b3f886cae0 -->

Implementation notes: Added AGENTS.md and updated .agents/skills/execute-tasks/SKILL.md with the CHANGELOG.md rule; updated .github/workflows/deploy.yml to pass --notes-file CHANGELOG.md on release creation/update and render CHANGELOG.md into web/index.html; added release notes section to web/index.html and web/style.css.
