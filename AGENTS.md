# Agent Guidelines for Open Tasks (`ot`)

This repository uses **Open Tasks (`ot` / `./oat`)** for repository-native task and planning management. All work items live in `.ot/tasks/` and meeting records in `.ot/meetings/`.

## Skills

- **Task Management**: See [`.agents/skills/task-management/SKILL.md`](.agents/skills/task-management/SKILL.md) for querying, creating, triaging, and validating tasks with `./oat`.
- **Executing Tasks**: See [`.agents/skills/execute-tasks/SKILL.md`](.agents/skills/execute-tasks/SKILL.md) for the step-by-step workflow when implementing tasks.

## Task Completion & `CHANGELOG.md` Rule

Whenever you complete a task:

1. **Update [`CHANGELOG.md`](CHANGELOG.md)**:
   - Append a concise bullet point summarizing the user-facing or technical change under the current heading in `CHANGELOG.md`, referencing the 6-character task short ID:
     ```markdown
     # Changes for version v0.1.4

     - Short description of what changed (`<short_id>`).
     ```
   - Include `CHANGELOG.md` in the per-task Git commit alongside the code, documentation, and `.ot/tasks/` updates.

2. **Release Reset Convention (Manual Post-Release Step)**:
   - `CHANGELOG.md` is used as the release notes source when publishing a GitHub Release and for displaying current release changes on the website.
   - After tagging and releasing version `vX.Y.Z`, a manual follow-up commit truncates `CHANGELOG.md` back to a single header for the next patch version (`# Changes for version vX.Y.(Z+1)`) and tags that commit as `vX.Y.(Z+1)-dev`. Do not remove or reset the header during normal task work.

