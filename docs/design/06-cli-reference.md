# CLI Reference

## Overview

This document describes the current and planned command-line interface for Open Tasks (ot).

This document is intended to describe user-facing behavior.

Implementation details belong in source code documentation.

Architecture rationale belongs in the ADRs.

The CLI is expected to evolve over time.

Commands described here should be treated as the intended user experience unless otherwise noted.

Related:

- ADR-0003 Unified WorkItem Model
- ADR-0009 Project Installed Tool Versions
- ADR-0010 Optional Wrapper Scripts
- ADR-0024 Markdown First Editing Workflow

---

# Command Structure

The primary command is:

```bash
ot
```

Optional project-local wrappers:

```bash
./oat
./oat.bat
```

Both interfaces are expected to provide identical behavior.

Most commands follow:

```bash
ot <category> <command> [options]
```

Examples:

```bash
ot task create
ot task show
ot meeting start
ot check
```

---

# Global Commands

## ot init

Initialize an OT project.

Example:

```bash
ot init
```

Specify a version:

```bash
ot init --version 1.2.3
```

Expected behavior:

- Create `.ot`
- Create default configuration
- Install project OT version
- Install default templates

Related:

- ADR-0009 Project Installed Tool Versions

---

## ot upgrade

Upgrade an existing project.

Example:

```bash
ot upgrade --version 1.3.0
```

Expected behavior:

- Download requested version
- Migrate configurations
- Migrate templates
- Preserve user data
- Perform transactional upgrade

Downgrades are currently not supported.

Related:

- ADR-0015 Transactional Upgrades

---

## ot check

Validate project state.

Example:

```bash
ot check
```

Checks may include:

- Configuration validation
- WorkItem integrity
- Relationship integrity
- Template integrity
- Attachment validation
- Reference validation

No changes are made.

---

## ot check --fix

Validate and repair project state.

Example:

```bash
ot check --fix
```

Expected behavior:

- Detect fixable problems
- Perform safe repairs
- Report unfixable problems

Related:

- ADR-0023 First Class Validation And Repair

---

## ot clean

Remove generated data.

Example:

```bash
ot clean --dry-run
```

or

```bash
ot clean --force
```

Exactly one of:

```text
--dry-run
--force
```

must be specified.

Current implementation status:

Planned.

No generated content currently requires cleanup.

---

# Work Item Commands

Note:

Historical command names use the word:

```text
task
```

because OT originally distinguished between Tasks and Epics.

These commands now operate on WorkItems.

The CLI may retain `task` for compatibility and familiarity.

---

## ot task create

Create a new WorkItem.

Example:

```bash
ot task create "Fix login button"
```

or

```bash
ot task create --title "Fix login button"
```

or

```bash
ot task create -m "Fix login button"
```

Additional options:

```bash
--overview
--edit
--no-edit
```

Behavior:

- Create WorkItem
- Generate UUID
- Apply template
- Optionally open editor

If required information is missing:

- Editor opens by default
- `--no-edit` converts missing information into an error

---

## ot task show

Display a WorkItem.

Example:

```bash
ot task show 4f2a9c
```

Expected output:

- Metadata
- Overview
- Description
- Comments
- Relationships

---

## ot task list

List WorkItems.

Example:

```bash
ot task list
```

Positional ID and multi-column/multi-value filtering examples:

```bash
ot task list 4f2a9c,8b1c0e

ot task list -s triage,planned -t bug,chore

ot task list --id 4f2a --title "Fix" --author "/@example\\.com$/"

ot task list --width 120
```

Output is intended to resemble summary tables (default width 120 columns when terminal width is `>= 120` or non-interactive, `80` when `< 120`, or overridden via `--width`).

---

## ot task update

Update WorkItem frontmatter fields or overview non-interactively via CLI flags.

Example:

```bash
ot task update 4f2a9c --title "New Title" --status in_progress --type bug --size medium --tag ui,urgent --overview "Updated summary"
```

---

## ot task edit

Edit a WorkItem.

Example:

```bash
ot task edit 4f2a9c
```

Behavior:

- Create temporary copy
- Open editor
- Validate changes
- Update canonical document

Validation failures prevent committing invalid changes.

Related:

- ADR-0024 Markdown First Editing Workflow

---

## ot task status

Update WorkItem status.

Example:

```bash
ot task status 4f2a9c completed
```

Note:

Future versions may consolidate this behavior into:

```bash
ot task edit
```

---

## ot task comment

Add a comment.

Example:

```bash
ot task comment 4f2a9c
```

Behavior:

- Open editor
- Create timestamped comment
- Include user identity

Comment format is template-driven.

---

# Relationship Commands

## ot task add-dependency

Create dependency relationship.

Example:

```bash
ot task add-dependency parent-id child-id
```

Meaning:

```text
child depends on parent
```

---

## ot task remove-dependency

Remove dependency relationship.

Example:

```bash
ot task remove-dependency parent-id child-id
```

---

## ot task get-dependencies

Display dependencies.

Example:

```bash
ot task get-dependencies 4f2a9c
```

Output may include:

- Parents
- Children
- Dependency parents
- Dependency children

---

# Meeting Commands

## ot meeting start

Begin a meeting.

Example:

```bash
ot meeting start --type grooming
```

or

```bash
ot meeting start -t grooming
```

Behavior:

- Create meeting record
- Apply template
- Record start time

Current meeting types:

```text
grooming
planning
retrospective
ideation
```

Project-specific meeting types may also exist.

---

## ot meeting end

End a meeting.

Example:

```bash
ot meeting end
```

Behavior:

- Record end time
- Update meeting record
- Remind user to publish changes

Future enhancements may include:

- Reviewer reminders
- Attendee verification reminders
- Meeting summaries

---

## ot meeting list

Display meeting information.

Example:

```bash
ot meeting list
ot meeting list --status active
ot meeting list --type grooming --json
```

---

# Attachment Commands

Status:

Implemented (see `ADR-0033`).

Attachments are stored in `<OwnerDir>/attachments/<filename>` and linked via relative Markdown links (`![label](attachments/<filename>)` for images or `[label](attachments/<filename>)` for other files).

---

## ot attachment add

Copy a file into `<OwnerDir>/attachments/` and append a relative Markdown link to the WorkItem or Meeting document.

Example:

```bash
ot attachment add 4f2a9c screenshot.png --label "Crash Screenshot"
```

---

## ot attachment remove

Remove an attachment file from `<OwnerDir>/attachments/` and strip its relative Markdown link from the WorkItem or Meeting document.

Example:

```bash
ot attachment remove 4f2a9c screenshot.png
```

---

## ot attachment list

List attachments for a WorkItem or Meeting.

Example:

```bash
ot attachment list 4f2a9c
ot attachment list 4f2a9c --json
```

---

## ot attachment show

Display metadata and path for a specific attachment.

Example:

```bash
ot attachment show 4f2a9c screenshot.png
ot attachment show 4f2a9c screenshot.png --json
```

---

# Configuration Commands

Status:

Implemented (`ot config get`, `ot config set`, `ot config list`).

---

## ot config get

Query a configuration value (`--show-origin`, `--json`).

Example:

```bash
ot config get user.editor
ot config get user.editor --show-origin
```

---

## ot config set

Set a configuration value, automatically routing protected keys (`system.*`, `workItem.*`, `meeting.*`, `paths.*`) to `.ot/config.json` and user keys (`user.*`) to `.ot/config.local.json` unless overridden via `--project` or `--local`.

Example:

```bash
ot config set user.editor code
```

Related:

- ADR-0016 Protected Configuration Keys

---

## ot config list

List effective configuration values (`--show-origin`, `--json`).

Example:

```bash
ot config list --show-origin
```

---

## ot schema

Export JSON Schema (Draft 2020-12) definitions for Open Tasks configuration (`config`), WorkItems (`work-item`), Meetings (`meeting`), or a bundle of all schemas (`all`).

Example:

```bash
ot schema
ot schema work-item
ot schema all --output schemas/
ot config schema
```

---

# Version Commands

## ot version

Proposed command.

Display:

- Wrapper version
- Project version

Example:

```bash
ot version
```

---

# Identifier Commands

Status:

Likely obsolete.

Examples:

```bash
ot id next

ot id next --claim
```

These commands originated from earlier monotonic identifier designs.

Future removal is likely.

See:

- OQ-0010 Monotonic Numeric Identifier Removal

---

# Exit Codes

Proposed behavior:

```text
0 = Success
1 = User error
2 = Validation failure
3 = Configuration error
4 = Upgrade error
5 = Internal error
```

Exact exit codes remain subject to refinement.

---

# Future Command Areas

Potential future command groups include:

```bash
ot sprint
ot report
ot search
ot export
ot import
```

No commitment has been made to implement these commands.

---

# Compatibility

Future versions should attempt to maintain reasonable CLI compatibility.

When behavior changes:

- Deprecation warnings should be preferred
- Migrations should be documented
- Upgrade guidance should be provided

---

# Open Questions

Related open questions:

- OQ-0002 Attachment Identifier Strategy
- OQ-0004 Sprint Representation
- OQ-0008 Work Item Short Identifier Implementation
- OQ-0010 Monotonic Numeric Identifier Removal
- OQ-0011 Active Meeting Tracking
- OQ-0018 Future Plugin and Extension Model
