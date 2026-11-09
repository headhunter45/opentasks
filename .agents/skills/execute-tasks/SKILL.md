---
name: execute-tasks
description: >-
  Execute and complete a specific list of tasks one by one. Use this skill
  whenever the user asks to work on, implement, execute, or do a specific set
  or batch of tasks (e.g. "Do tasks 075920, 29ba55", "Work on these tasks
  one at a time"). Validates task statuses, executes implementation
  sequentially, updates documentation, marks tasks completed, records follow-up
  tasks, and creates git commits per task.
---

# Execute Tasks Workflow Skill

This skill defines the standardized procedure for executing a specific set of tasks sequentially with strict status validation, documentation updates, follow-up tracking, and per-task commits.

Tasks are managed with Open Tasks via the project wrapper `./oat` (see the `task-management` skill). Tasks may be referenced by 6-character short ID, UUID, or title.

---

## 1. Task Status Validation & Confirmation

Before starting execution on any given task, inspect its status using `./oat task show <ID>`:

- **Valid Statuses to Work On**:
  - `planned` (Ready for implementation)
  - `in_progress` (Work currently active)

- **Invalid / Ambiguous Statuses**:
  - `triage`: Requirements, prioritization, or technical approach unconfirmed.
  - `blocked`: Task is waiting on external dependencies or decisions.
  - `completed`: Task is already finished.
  - `closed`: Task was archived or cancelled.

> [!WARNING]
> **Status Check Rule**: If any requested task is in an invalid status (`triage`, `blocked`, `completed`, or `closed`), you **must stop, report the task ID and its current status to the user, explain why it is not ready for implementation, and ask for explicit confirmation** before proceeding with that task.

---

## 2. Step-by-Step Task Execution Loop

Process each validated task **strictly one at a time** in the requested order:

```mermaid
graph TD
    A[Inspect & Validate Task Status] --> B[Mark Task In Progress]
    B --> C[Implement Code & Fixes]
    C --> D[Run Tests & Project Check]
    D --> E[Update Relevant Documentation]
    E --> F[Comment & Mark Completed]
    F --> G[Add Discovered Follow-Up Tasks as Triage]
    G --> H[Create Git Commit for Task]
    H --> I{More Tasks?}
    I -- Yes --> A
    I -- No --> J[Report Completion Summary]
```

### Step A: Mark In Progress
```bash
./oat task status <ID> in_progress
```

### Step B: Implement Requirements
1. Read the task using `./oat task show <ID>`.
2. Inspect the relevant source files in `src/ot/` and implement the requested changes, adhering to the ADRs in `docs/design/adrs/`.
3. If partial implementation is required or edge cases emerge, record notes with `./oat task comment <ID> "..."`.

### Step C: Verify & Test
Run the test suite and project integrity check to ensure no regressions:
```bash
PYTHONPATH=src python3 -m unittest discover -s tests
./oat check
```
For changes affecting packaging or releases, also run:
```bash
./scripts/build-release --version 0.0.0-dev
```

### Step D: Update Documentation & `CHANGELOG.md`
1. **Update [`CHANGELOG.md`](../../../CHANGELOG.md)** (Mandatory on every completed task):
   - Append a concise bullet point describing what changed (e.g., `- <concise summary of change> (<ID>)`) under the `# Changes for version ...` heading in `CHANGELOG.md`.
   - *(Note: `CHANGELOG.md` is used for GitHub Releases and the website, and is manually truncated/reset to the next version heading `# Changes for version vX.Y.(Z+1)` in a `-dev`-tagged commit immediately after each release.)*
2. Check if the changes affect:
   - [README.md](../../../README.md)
   - Design specifications or ADRs in `docs/design/`
   - The web portal in `web/` (`index.html`, `install.sh`)

Update the corresponding files accordingly.

### Step E: Mark Task Completed
```bash
./oat task comment <ID> "Implementation notes: <summary>. Follow-up logged in <ID>."
./oat task status <ID> completed
```

### Step F: Record Newly Discovered Tasks
If any new bugs, edge cases, refactor opportunities, or follow-ups are discovered, log them immediately in `triage` status:
```bash
./oat task create \
  --title "Follow-up: <Descriptive Title>" \
  --type <feature|bug|chore|spike> \
  --status triage \
  --overview "Discovered during work on <ID>." \
  --no-edit
```

### Step G: Create Git Commit
Create a dedicated Git commit for the completed task, including `CHANGELOG.md` and its `.ot/tasks/` changes:
```bash
git add <modified-files> CHANGELOG.md .ot/
git commit -m "<type>(open-tasks): <concise summary> (<ID>)"
```
*(At least one commit must be made per completed task before moving to the next task).*
