# ADR-0036 - Configurable Content Directory Paths Within Project Root

Status:
Accepted

Context:

By default, Open Tasks stores all project data beneath `.ot/` (ADR-0029):

- `.ot/bin/`
- `.ot/config.json`
- `.ot/config.local.json`
- `.ot/tasks/`
- `.ot/meetings/`
- `.ot/templates/`

However, some teams want their tasks, meetings, or templates stored in visible repository directories outside `.ot/` (for example, `docs/tasks/`, `docs/meetings/`, or `docs/templates/`) so they are immediately browsable as project documentation in GitHub, GitLab, or Obsidian (`OQ-0016`).

Decision:

1. **Fixed Tool & Configuration Paths**:
   - `.ot/` remains the canonical project root marker used for project discovery (ADR-0028).
   - `.ot/bin/`, `.ot/config.json`, and `.ot/config.local.json` remain at their fixed canonical locations inside `.ot/`.
2. **Configurable Content Directory Paths Under the Project Root**:
   - Projects may relocate the `tasks`, `meetings`, and `templates` directories anywhere within the project root (the parent directory of `.ot/`) via the `paths` section in `.ot/config.json`:
     ```json
     {
       "paths": {
         "tasks": "docs/tasks",
         "meetings": "docs/meetings",
         "templates": ".ot/templates"
       }
     }
     ```
   - `paths.tasks`, `paths.meetings`, and `paths.templates` are protected project-level configuration keys (`PROTECTED_CONFIG_KEYS` in `src/ot/config.py`).
3. **Project Root Containment Boundary**:
   - Configured paths are resolved relative to the project root (the parent directory of `.ot/`) and **must** resolve to a path inside the project root directory.
   - Any configured path that escapes the project root (e.g., `../outside` or an external absolute path) shall be rejected as a configuration validation error.

Reasoning:

- Keeping `.ot/config.json` and `.ot/bin/` at fixed locations ensures the launcher and configuration loader can always bootstrap deterministically without circular configuration lookups.
- Allowing `tasks`, `meetings`, and `templates` to live anywhere under the parent directory of `.ot/` lets projects expose planning artifacts as first-class visible documentation (`docs/tasks/`, `planning/meetings/`, etc.) while keeping all data repository-native (ADR-0001).
- Enforcing that resolved paths stay within the project root prevents accidental or malicious writes outside the repository.

Alternatives Considered:

### Hardcoded `.ot/{tasks,meetings,templates}` Only

Pros:

- Slightly simpler path resolution

Cons:

- Hidden `.ot/` folders are less visible in some documentation browsers and code forges when teams want tasks/meetings published alongside `docs/`

### Allowing Arbitrary Paths Outside the Project Root

Pros:

- Maximum flexibility

Cons:

- Violates repository-native storage (ADR-0001) and creates security and portability hazards

Consequences:

Positive:

- Teams can expose tasks, meetings, and templates as visible repository documentation (e.g., `docs/tasks/`)
- Deterministic bootstrap because `.ot/config.json` and `.ot/bin/` never move
- Safe containment within the project root

Negative:

- Scanner, template loader, meeting commands, and validator must resolve `tasks`, `meetings`, and `templates` directories through `Config` rather than hardcoding `.ot/<subdir>`

## Amendments (As-Built)

- **Implementation Tracking**: Implementing `paths.{tasks,meetings,templates}` resolution, containment validation, and adding `paths` to `PROTECTED_CONFIG_KEYS` is tracked in task `97aa42`.
