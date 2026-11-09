---
id: 829b918a-e163-4ce3-bc28-82d624fb5400
title: Support release candidate tags (vX.Y.Z-rc.N) in deploy workflow
type: feature
status: completed
size: small
created_at: 2026-11-09T22:55:36.207474+00:00
updated_at: 2026-11-09T22:57:29.791544+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
tags:
  - feature
---

# Support release candidate tags (vX.Y.Z-rc.N) in deploy workflow

## Summary

Describe the user-facing feature or enhancement.

## Requirements

- [ ] Requirement 1
- [ ] Requirement 2

## Design / Technical Notes

Architecture decisions and technical implementation details.

## Overview
Update .github/workflows/deploy.yml to build and publish GitHub Pre-releases for vX.Y.Z-rc.N tags without deploying the website.

## Comments

### Comment by Tom Hicks <headhunter3@gmail.com> on 2026-11-09T22:57:29.314924+00:00
<!-- comment-id: e4999e54-b2e6-46b7-9690-fcc8e76f0e91 -->

Updated .github/workflows/deploy.yml to trigger on vX.Y.Z-rc.N tags, publish GitHub Pre-releases (--prerelease) without deploying GitHub Pages, and added SemVer numeric pre-release comparison and unit tests.
