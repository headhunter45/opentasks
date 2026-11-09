---
id: d244b044-efcb-44bb-a716-fa66bc0fad3d
title: Filter non-release tags in deploy workflow and resolve latest release ancestor tag
type: chore
status: completed
size: small
created_at: 2026-11-09T05:06:59.681056+00:00
updated_at: 2026-11-09T05:08:06.766525+00:00
parent: 29a5aa6d-eaac-4feb-bf1d-015003fd679b
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Filter non-release tags in deploy workflow and resolve latest release ancestor tag

## Overview
Ensure .github/workflows/deploy.yml ignores pre-release/dev tags (like v0.1.3-dev) in tag triggers and release publishing, and when triggered on main resolves the nearest ancestor tag matching ^v[0-9]+(\.[0-9]+(\.[0-9]+)?)?$ (e.g. v0.1.2) for website deployment.

## Comments

### Comment by Tom Hicks <headhunter3@gmail.com> on 2026-11-09T05:08:06.314965+00:00
<!-- comment-id: 14c57278-8724-4bf0-afc5-bb83b67168e8 -->

Implementation notes: Updated .github/workflows/deploy.yml to ignore pre-release/dev tags (!v*-*) in on.push.tags, check tags against ^v[0-9]+(\.[0-9]+(\.[0-9]+)?)?$ for release publishing, and resolve the greatest ancestor release tag via git tag --merged HEAD --sort=-v:refname when deploying from main.
