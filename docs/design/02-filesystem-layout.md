# Filesystem Layout

## Overview

This document describes the default filesystem layout used by Open Tasks (ot).

All paths described in this document are relative to the project root unless otherwise specified.

The filesystem layout is designed to support:

- Repository-native operation
- Human-readable project data
- Source-control-friendly workflows
- Direct file editing
- Offline usage
- Future schema evolution

Related:

- ADR-0001 Repository Native Storage
- ADR-0013 Configuration Stored Under .ot
- ADR-0026 Work Item Filesystem Ownership
- ADR-0029 .ot Directory As Canonical Tool Root

---

## Project Root

The project root is the root directory of an OT project.

The project root may contain:

```text
oat
oat.bat
.ot/
```

No additional OT-managed files are expected at the root by default.

### Wrapper Scripts

Wrapper scripts are optional.

Recommended names:

```text
oat
oat.bat
```

Wrapper scripts exist outside `.ot` because they are intended to be executed directly by users and automation systems.

See:

- ADR-0010 Optional Wrapper Scripts

---

## The .ot Directory

The `.ot` directory is the canonical root for all OT-managed project state.

The default layout is:

```text
.ot/
  bin/
  config.json
  config.local.json
  tasks/
  meetings/
  templates/
```

All paths except `.ot/bin` and configuration files may eventually support relocation through configuration.

See:

- ADR-0029 .ot Directory As Canonical Tool Root

---

## Configuration

### Repository Configuration

```text
.ot/config.json
```

This file is intended to be checked into source control.

Examples:

- Work item type definitions
- Status definitions
- Meeting types
- Templates
- Shared project configuration

### Local Overrides

```text
.ot/config.local.json
```

This file is not intended to be checked into source control.

Examples:

- User identity
- Preferred editor
- Local developer overrides

### Schema Version Compatibility

The schema versions of:

```text
config.json
config.local.json
```

must be compatible.

Schema mismatches are treated as errors.

See:

- ADR-0011 Configuration Layering
- ADR-0012 Configuration Precedence Order
- ADR-0013 Project and User Configuration Separation

---

## Executables And Runtime Files

### Tool Installation

```text
.ot/bin/
```

contains OT implementation files.

Examples:

```text
.ot/bin/0.1.3/ot.zipapp
.ot/bin/0.1.3/ot-manifest.json
```

Files in this directory are managed by OT.

This directory should not be checked into source control.

### Versioned Installation

Projects use a project-installed version of OT.

The globally installed `ot` command acts as a launcher.

See:

- ADR-0009 Project Installed Tool Versions

---

## Work Items

### Root Directory

```text
.ot/tasks/
```

contains all work item content.

Work items form a logical hierarchy.

The exact filesystem representation remains under evaluation.

See:

- OQ-0001 Final Work Item Filesystem Layout

---

## Current Candidate Structure

Current preferred structure:

```text
.ot/tasks/
  ReleaseAlpha/
    index.md

    Attachments/

    UserAuthentication/
      index.md

      LoginPage/
        index.md

      AccountRecovery/
        index.md
```

In this model:

- Every work item owns a directory.
- The primary document is `index.md`.
- Child work items exist beneath their parent.
- Attachments belong to the work item subtree.

This approach is currently preferred but not finalized.

Related:

- ADR-0026 Work Item Filesystem Ownership
- OQ-0001 Final Work Item Filesystem Layout

---

## Attachments

Attachments may be:

- Images
- Documents
- Diagrams
- Other reference material

Current preferred layout:

```text
SomeWorkItem/
  index.md
  attachments/
```

Example:

```text
SomeWorkItem/
  index.md
  attachments/
    screenshot.png
    design.pdf
```

### Ownership Model

Attachments belong to the work item subtree in which they reside.

Shared attachment behavior remains under discussion.

See:

- OQ-0017 Attachment Ownership Rules

---

## Meetings

### Root Directory

```text
.ot/meetings/
```

contains meeting artifacts.

Meetings are organized by meeting type.

Current preferred structure:

```text
.ot/meetings/
  grooming/
  planning/
  retrospective/
  ideation/
```

Example:

```text
.ot/meetings/
  grooming/
    2026-08-12T09-00-00.md
```

### Meeting Attachments

Current proposal:

```text
.ot/meetings/
  grooming/
    attachments/
```

The exact attachment strategy remains open.

See:

- OQ-0005 Meeting Storage Details

---

## Templates

### Root Directory

```text
.ot/templates/
```

Templates are user-editable files used to generate OT content.

Templates are intended to be checked into source control.

See:

- ADR-0014 Template Based Content Generation
- ADR-0022 Template Customization Over Code Customization

---

### Task Templates

```text
.ot/templates/tasks/
```

Examples:

```text
default.md
bug.md
enhancement.md
```

Exact template structure remains configurable.

---

### Meeting Templates

```text
.ot/templates/meetings/
```

Examples:

```text
grooming.md
planning.md
retrospective.md
ideation.md
```

Meeting type names should correspond to configured meeting types.

---

### Shared Templates

```text
.ot/templates/shared/
```

Examples:

```text
comment.md
attachment.md
```

Shared templates may be reused across work items and meetings.

--
