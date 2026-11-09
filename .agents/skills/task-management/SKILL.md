---
name: task-management
description: >-
  Manage, query, create, triage, inspect, and update project tasks using Open Tasks
  (ot / ./oat). Activate this skill whenever reading, creating, editing, prioritizing,
  or updating tasks, checklists, or project progress.
---

# Task Management Skill

This skill provides operational guidelines and procedures for managing project tasks using **Open Tasks (`ot` / `./oat`)**. All tasks, epics, bugs, and meeting records are stored directly in the repository under `.ot/tasks/` and `.ot/meetings/`.

---

## Quick Reference

In the repository root, run commands through the self-hosted wrapper `./oat` (or the global `ot` CLI):

```bash
# Verify project version and health
./oat version
./oat check
```

---

## Core Procedures

### 1. Querying and Inspecting Tasks

- **List active work items**:
  ```bash
  ./oat task list
  ```
- **Filter by status**:
  ```bash
  ./oat task list --status planned
  ./oat task list --status in_progress
  ./oat task list --status completed
  ./oat task list --status blocked
  ```
- **Filter by type**:
  ```bash
  ./oat task list --type epic
  ./oat task list --type feature
  ./oat task list --type bug
  ./oat task list --type chore
  ```
- **Inspect a specific task** (by 6-char short ID, UUID, or title):
  ```bash
  ./oat task show 075920
  ./oat task show "Cleanup source tree."
  ```

---

### 2. Creating WorkItems

Create new tasks using template instantiation:

```bash
./oat task create \
  --title "Implement Cache Invalidation" \
  --type feature \
  --status planned \
  --size medium \
  --parent "Distribution and Release System" \
  --overview "Support explicit cache invalidation in ot upgrade." \
  --no-edit
```

Available types: `feature`, `bug`, `task`, `chore`, `spike`, `epic`.
Available statuses: `triage`, `planned`, `in_progress`, `blocked`, `completed`, `closed`.
Available sizes: `small`, `medium`, `large`.

---

### 3. Updating Lifecycles & Recording Progress

- **Update Task Status**:
  ```bash
  ./oat task status "Implement Cache Invalidation" in_progress
  ./oat task status "Implement Cache Invalidation" completed
  ```
- **Append Timestamped Comment**:
  ```bash
  ./oat task comment "Implement Cache Invalidation" "Implemented cache clearing on version mismatch."
  ```
- **Add Task Dependency / Blocker**:
  ```bash
  ./oat task add-dependency "Implement Cache Invalidation" "Build Cache Management"
  ```

---

### 4. Integrity Validation & Automatic Repair

Run diagnostic checks before concluding tasks or submitting PRs:

```bash
# Check repository integrity (UUID uniqueness, relationships, schema validity)
./oat check

# Output diagnostics as JSON
./oat check --json

# Automatically repair trivial inconsistencies
./oat check --fix
```
