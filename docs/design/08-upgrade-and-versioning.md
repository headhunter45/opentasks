# Upgrade and Versioning

## Overview

This document describes version selection, installation, initialization, upgrades, and migrations within Open Tasks (ot).

OT separates:

- The globally installed launcher
- The project-installed implementation

This allows projects to use specific OT versions independently of the version installed on a developer workstation.

Related:

- ADR-0009 Project Installed Tool Versions
- ADR-0010 Optional Wrapper Scripts
- ADR-0015 Transactional Upgrades

---

# Design Goals

The versioning system should:

- Allow different projects to use different OT versions
- Avoid global version conflicts
- Support reproducible project behavior
- Minimize installation requirements
- Support offline and repository-native workflows
- Support future schema migrations
- Avoid partial upgrades

---

# Terminology

## Launcher

The launcher is the globally installed executable.

Examples:

```text
ot
```

Responsibilities:

- Locate the project
- Discover the configured version
- Validate installation state
- Download required versions
- Launch the correct implementation

The launcher is not responsible for project logic.

---

## Project Implementation

The project implementation is the versioned OT executable installed for a specific project.

Example:

```text
.ot/bin/ot.py
```

The implementation executes commands such as:

```text
task create
task edit
meeting start
meeting end
check
```

---

## Project Version

The project version is the version specified by project configuration.

Example:

```json
{
  "system": {
    "toolVersion": "1.2.3"
  }
}
```

The exact configuration schema remains subject to refinement.

---

# Installation Model

## Global Installation

Users install the launcher once.

Examples:

```text
/usr/bin/ot
~/bin/ot
```

or equivalent platform locations.

The launcher is expected to work across multiple projects.

---

## Project Installation

Projects install a specific OT implementation beneath:

```text
.ot/bin/<version>/
```

Example:

```text
.ot/bin/0.1.1/ot.zipapp
.ot/bin/0.1.1/ot-manifest.json
```

Previously downloaded project versions are preserved in their respective `.ot/bin/<version>/` directories, and `.ot/bin/` is ignored from source control. Multiple projects may use different versions simultaneously.

---

# Python Requirements

OT requires a supported version of Python on the host system.

Projects should not require:

- Project-specific Python installations
- Project-specific Python distributions
- Project-specific virtual environments

Current direction:

A single host Python installation should be reusable across all OT projects.

Related:

- OQ-0014 Global OT Cache Structure

---

# Version Selection

## Version Source

Version selection is determined by project configuration.

Example:

```text
.ot/config.json
```

The configured version is authoritative.

---

## Version Validation

The launcher validates:

- Configured version
- Installed version
- Available implementation

Example failure:

```text
Configured: 1.3.0
Installed: 1.2.0
```

This is an error condition.

The mismatch must be resolved before normal operation continues.

---

# Initialization

## Purpose

Initialization creates a new OT project.

Example:

```bash
ot init
```

or:

```bash
ot init --version 1.2.3
```

---

## Initialization Responsibilities

Initialization should:

- Create `.ot`
- Create configuration files
- Create default templates
- Install the requested implementation
- Create required folders
- Ensure `.ot/bin/` is listed in `.gitignore`

Example:

```text
.ot/
  bin/
  config.json
  config.local.json
  tasks/
  meetings/
  templates/
```

---

## Version Selection During Initialization

If a version is specified:

```bash
ot init --version 1.2.3
```

that version becomes authoritative.

If no version is specified:

The launcher's version may be used as the default.

---

# Upgrades

## Purpose

Upgrades move a project to a newer OT version.

Example:

```bash
ot upgrade --version 1.3.0
```

---

## Upgrade Rules

### Valid Upgrade

Example:

```text
Current: 1.2.0
Target: 1.3.0
```

Allowed.

---

### Upgrade To Same Version

Example:

```text
Current: 1.2.0
Target: 1.2.0
```

Should produce:

```text
Warning
```

or

```text
No-op error
```

Implementation decision may vary.

---

### Downgrade

Example:

```text
Current: 1.3.0
Target: 1.2.0
```

Not supported.

Downgrades are treated as errors.

---

### Invalid Version

Example:

```text
ot upgrade --version abc
```

Error.

Version strings must be valid.

Current expectation is semantic versioning.

---

### Missing Version

Example:

```text
ot upgrade --version 99.99.99
```

if unavailable.

Error.

No local changes should occur.

---

# Transactional Upgrade Process

## Goal

Projects should never be left partially upgraded.

---

## Process

Current expected flow:

1. Validate target version.
2. Download target version.
3. Create temporary upgrade workspace.
4. Copy current configuration.
5. Copy required project data.
6. Run migration logic.
7. Validate migration results.
8. Replace existing installation.
9. Clean temporary workspace.

If any step fails:

- Existing installation remains unchanged.
- Existing configuration remains unchanged.
- Existing templates remain unchanged.

See:

- ADR-0015 Transactional Upgrades

---

# Template Migration

Templates are user-editable.

Upgrades must preserve modifications whenever practical.

Questions remain regarding:

- Automatic replacement
- Backup strategy
- Merge strategy
- User prompts

See:

- OQ-0006 Template Migration Behavior

---

# Schema Migration

Configuration schemas may evolve.

Future upgrades may perform migrations for:

```text
Configuration
Work Items
Meetings
Templates
Relationships
```

Schema migration must occur during upgrade.

The exact schema strategy remains under discussion.

See:

- OQ-0007 Configuration Schema Evolution

---

# Global Cache

Future implementations may cache downloaded artifacts.

Potential location:

```text
~/.ot/
```

Examples:

```text
~/.ot/cache/
~/.ot/versions/
```

The cache may be shared between projects.

Cache structure remains unresolved.

See:

- OQ-0014 Global OT Cache Structure

---

# Wrapper Scripts

## Optional Project Wrappers

Projects may contain:

```text
oat
oat.bat
```

These wrappers are optional.

Their purpose is to support:

- CI systems
- Shared environments
- Restricted installations

Normal users are expected to use:

```bash
ot
```

---

## Wrapper Responsibilities

Wrappers should:

- Locate project root
- Invoke the launcher
- Preserve command-line arguments

They should not contain project logic.

See:

- ADR-0010 Optional Wrapper Scripts

---

# Version Discovery

Version discovery currently follows:

1. Locate project root.
2. Read project configuration.
3. Determine configured version.
4. Validate installation.
5. Launch matching implementation.

Project configuration is authoritative.

---

# Version Mismatch Handling

Examples:

## Missing Implementation

```text
Configured version exists.
Installed implementation missing.
```

Error.

---

## Wrong Implementation

```text
Configured version: 1.3.0
Installed version: 1.2.0
```

Error.

---

## Corrupted Installation

```text
Implementation missing required files.
```

Error.

---

## Schema Version Mismatch

Example:

```text
config.json
config.local.json
```

contain incompatible schema versions.

Error.

Migration or repair is required.

---

# Validation Responsibilities

Validation should verify:

- Installed implementation exists
- Installed implementation matches configuration
- Required files exist
- Templates exist
- Schema versions are compatible

Validation is performed through:

```bash
ot check
```

and

```bash
ot check --fix
```

---

# Future Considerations

Potential future capabilities include:

- Shared version caches
- Cached downloads
- Upgrade previews
- Rollback support
- Automatic artifact verification

No commitment has been made to implement these features.

---

# Open Questions

Related open questions:

- OQ-0006 Template Migration Behavior
- OQ-0007 Configuration Schema Evolution
- OQ-0014 Global OT Cache Structure

Future versioning decisions should be evaluated against OT's goals of reproducibility, portability, and repository-native operation.
