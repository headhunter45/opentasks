# Open Questions

This document tracks unresolved design questions for Open Tasks (ot).

Questions recorded here should eventually result in one of the following outcomes:

- Accepted architecture decision (ADR)
- Rejected architecture decision
- Design document clarification
- Removal if no longer relevant

Questions should remain here until a decision is documented elsewhere.

---

# OQ-0001 - Final Work Item Filesystem Layout

Status:
Closed (Resolved by ADR-0026)

Resolution:

Option B (`<PascalCaseSanitizedTitle>/index.md`, with child work items nested beneath their parent work item's directory) was implemented and accepted in [ADR-0026](adrs/ADR-0026-work-item-filesystem-ownership.md).

---

# OQ-0002 - Attachment Identifier Strategy

Status:
Closed (Resolved by ADR-0033)

Resolution:

Attachments do not require separate UUIDs; they are stored in `<OwnerDir>/attachments/<filename>` and referenced via standard relative Markdown links. Documented in [ADR-0033](adrs/ADR-0033-attachment-storage-and-validation-scope.md).

---

# OQ-0003 - Attachment Metadata Model

Status:
Closed (Resolved by ADR-0033)

Resolution:

Attachments do not use sidecar metadata files or YAML frontmatter registries; authorship and timestamps are tracked through standard repository history, and links live in the parent Markdown file. Documented in [ADR-0033](adrs/ADR-0033-attachment-storage-and-validation-scope.md).

---

# OQ-0004 - Sprint Representation

Status:
Deferred

Summary:

Sprints have not yet been modeled. Kept deferred until core WorkItem, Meeting, Attachment, Configuration, and Validation tasks are completed.

Potential approaches:

Option A:

Represent sprints as WorkItems.

Option B:

Represent sprints as a dedicated model.

Questions:

- Do sprints require unique fields?
- Do sprints require unique validation?
- Do sprints require unique reporting?

---

# OQ-0005 - Meeting Storage Details

Status:
Closed (Resolved by ADR-0034)

Resolution:

Each meeting owns a directory beneath `.ot/meetings/<meeting-type>/<YYYY-MM-DDTHH-MM-SS>/` (or the configured `paths.meetings` directory) containing `index.md` and an optional `attachments/` subdirectory. Documented in [ADR-0034](adrs/ADR-0034-meeting-storage-and-lifecycle-tracking.md).

---

# OQ-0006 - Template Migration Behavior

Status:
Closed (Resolved by ADR-0035)

Resolution:

User-modified templates in `.ot/templates/` are never overwritten during `ot upgrade`. Checksum comparison against known default templates updates untouched default templates automatically while preserving user-modified templates and writing `<template>.default` when upstream changes occur. Documented in [ADR-0035](adrs/ADR-0035-template-and-schema-migrations.md).

---

# OQ-0007 - Configuration Schema Evolution

Status:
Closed (Resolved by ADR-0035)

Resolution:

Configuration schema versioning uses a single integer `system.configSchemaVersion` migrated sequentially (`v1 -> v2`, etc.) inside the transactional upgrade staging workspace. Documented in [ADR-0035](adrs/ADR-0035-template-and-schema-migrations.md).

---

# OQ-0008 - Work Item Short Identifier Implementation

Status:
Closed (Resolved by ADR-0008)

Resolution:

Short identifiers are derived directly from canonical UUIDv4 strings (hyphens stripped, lowercase) with a default display length of 6 hex characters (automatically extended if needed for uniqueness) and a minimum accepted query prefix of 4 hex characters. Documented in [ADR-0008](adrs/ADR-0008-git-style-short-identifiers.md).

---

# OQ-0009 - Work Item Relationship Representation

Status:
Closed (Resolved by ADR-0032)

Resolution:

Relationships (`parent` and `dependencies`) are stored unidirectionally as canonical UUIDs in the child/dependent WorkItem's YAML frontmatter, and inverse relationships (`children` and `dependents`/`blocks`) are computed in memory by `WorkItemIndex`. Documented in [ADR-0032](adrs/ADR-0032-yaml-frontmatter-and-unidirectional-relationships.md).

---

# OQ-0010 - Monotonic Numeric Identifier Removal

Status:
Closed (Resolved by ADR-0007 and ADR-0008)

Resolution:

Monotonic numeric counters (`system.next_id_number`, `ot id next`) were removed completely in favor of UUIDv4 canonical identifiers and Git-style short hex prefixes.

---

# OQ-0011 - Active Meeting Tracking

Status:
Closed (Resolved by ADR-0034)

Resolution:

Active meetings are tracked directly via `status: active | ended`, `started_at`, and `ended_at` in the YAML frontmatter of `.ot/meetings/<type>/<timestamp>/index.md` without a separate session lock file. Documented in [ADR-0034](adrs/ADR-0034-meeting-storage-and-lifecycle-tracking.md).

---

# OQ-0012 - Work Item Display Naming

Status:
Closed (Resolved by ADR-0026)

Resolution:

WorkItem directories are named `<PascalCaseSanitizedTitle>/` (up to the first 6 alphanumeric words of the title, or `Task-<short_id>` if untitled) with `index.md` inside. Because identity and relationships use UUIDs in frontmatter, directory names remain stable or can be renamed without breaking references. Documented in [ADR-0026](adrs/ADR-0026-work-item-filesystem-ownership.md).

---

# OQ-0013 - Validation Scope

Status:
Closed (Resolved by ADR-0033)

Resolution:

`ot check` validates all OT-managed files plus relative Markdown links within the repository (including local `attachments/` and relative links to files under the project root), warns on orphaned files in `attachments/` without deleting them, and does not make network requests for external `http(s)://` URLs. Documented in [ADR-0033](adrs/ADR-0033-attachment-storage-and-validation-scope.md).

---

# OQ-0014 - Global OT Cache Structure

Status:
Closed (Resolved by ADR-0009 and ADR-0013)

Resolution:

Global user data lives under `~/.ot/` (or `$OT_USER_HOME`), with `~/.ot/config.json` for global user configuration and `~/.ot/versions/<version>/ot.zipapp` (+ `ot-manifest.json`) for cached release artifacts shared across projects. Documented in [ADR-0009](adrs/ADR-0009-project-installed-tool-versions.md) and [ADR-0013](adrs/ADR-0013-project-and-user-configuration-separation.md).

---

# OQ-0015 - Future Version Control Support

Status:
Closed (Resolved by ADR-0004, ADR-0005, and ADR-0030)

Resolution:

Git and Mercurial are supported via CLI queries (`git config` and `hg config` in `src/ot/discovery.py`, task `3109b3`) and `.git`/`.hg` root detection; any unrecognized or absent VCS falls back cleanly to No-VCS environment and system defaults.

---

# OQ-0016 - Repository Layout Overrides

Status:
Closed (Resolved by ADR-0036)

Resolution:

`.ot/bin/`, `.ot/config.json`, and `.ot/config.local.json` remain fixed inside `.ot/`, while `tasks`, `meetings`, and `templates` directories can be redirected anywhere within the project root (the parent directory of `.ot/`) via `paths.tasks`, `paths.meetings`, and `paths.templates` in `.ot/config.json`. Documented in [ADR-0036](adrs/ADR-0036-configurable-content-directory-paths.md).

---

# OQ-0017 - Attachment Ownership Rules

Status:
Closed (Resolved by ADR-0033)

Resolution:

Each WorkItem or Meeting owns an `attachments/` subfolder inside its own directory (`<OwnerDir>/attachments/<file>`). Unreferenced files inside `attachments/` are reported as warnings by `ot check` and are never automatically deleted. Documented in [ADR-0033](adrs/ADR-0033-attachment-storage-and-validation-scope.md).

---

# OQ-0018 - Future Plugin and Extension Model

Status:
Deferred

Summary:

No plugin system is planned; template customization (ADR-0022) and external import/export tools consuming open repository formats or JSON CLI output (ADR-0018, ADR-0019) remain the preferred extension mechanisms.
