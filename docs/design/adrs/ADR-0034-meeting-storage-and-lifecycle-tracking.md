# ADR-0034 - Meeting Directory Layout And Frontmatter Lifecycle State

Status:
Accepted

Context:

Open Tasks models planning meetings (`grooming`, `planning`, `retrospective`, `ideation`, and custom project types) as repository-native Markdown artifacts (`05-meetings-and-planning.md`, `06-cli-reference.md`).

Two open questions (`OQ-0005` and `OQ-0011`) remained unresolved:

1. How should meeting files and their attachments be organized beneath `.ot/meetings/` (or the configured meetings directory)?
2. How should active meetings (`ot meeting start`, `ot meeting end`, `ot meeting list`) be tracked without introducing fragile out-of-band session state?

Decision:

1. **Directory-Per-Meeting Layout**:
   - Mirroring WorkItem filesystem ownership (ADR-0026), each meeting owns a directory beneath its meeting type folder using an ISO-like timestamp directory name (`YYYY-MM-DDTHH-MM-SS`), with `index.md` as the primary document and an optional `attachments/` subdirectory:
     ```text
     .ot/meetings/<meeting-type>/<YYYY-MM-DDTHH-MM-SS>/
       index.md
       attachments/
     ```
2. **YAML Frontmatter Lifecycle State**:
   - Active vs. ended meeting state and metadata are recorded directly in the YAML frontmatter of the meeting's `index.md` document:
     - `id`: canonical UUIDv4 of the meeting
     - `type`: configured meeting type (e.g., `grooming`, `planning`, `retrospective`, `ideation`)
     - `status`: `active` (when started via `ot meeting start`) or `ended` (when completed via `ot meeting end`)
     - `started_at`: UTC ISO-8601 start timestamp
     - `ended_at`: UTC ISO-8601 end timestamp (populated by `ot meeting end`)
     - `organizer`: author object (`name`, `email`)
     - `attendees`: list of attendee strings or objects
3. **No Separate Session Lock File**:
   - `ot meeting list` and `ot meeting end` discover active meetings by scanning the meetings directory for `index.md` documents with `status: active`, rather than relying on a separate `.active` pointer file.

Reasoning:

- Giving each meeting its own directory (`<timestamp>/index.md`) provides a consistent ownership model across both WorkItems and Meetings and gives meeting attachments a natural home (`attachments/`).
- Storing `status: active | ended` inside `index.md` keeps the meeting document self-contained, reviewable in Git, and immune to stale pointer files if a branch is switched or a file is edited manually.

Alternatives Considered:

### Flat Markdown Files (`.ot/meetings/<type>/<timestamp>.md`)

Pros:

- One fewer directory level when a meeting has no attachments

Cons:

- Inconsistent with WorkItem `<Folder>/index.md` layout (ADR-0026)
- No dedicated per-meeting `attachments/` directory

### Separate Active Session Pointer File (`.ot/meetings/.active`)

Pros:

- Instant lookup without scanning meeting files

Cons:

- Easily becomes out of sync if users edit meeting files directly or switch branches

Consequences:

Positive:

- Unified `<Folder>/index.md` + `attachments/` pattern across WorkItems and Meetings
- Self-contained, branch-safe active meeting tracking
- Directly editable in any text editor

Negative:

- `ot meeting list` and `ot meeting end` scan the meetings directory to locate active meetings

## Amendments (As-Built)

- **Implemented Meeting Model, Storage, and CLI (`src/ot/models.py`, `src/ot/parser.py`, `src/ot/cli.py`, `src/ot/validation.py`)**:
  - `ot meeting start` renders `.ot/templates/meetings/<type>.md` into `<meetings_dir>/<type>/<YYYY-MM-DDTHH-MM-SS>/index.md` with `id`, `type`, `status: active`, `started_at`, `organizer`, and `attendees` in YAML frontmatter (task `a9baac`).
  - `ot meeting end [<id_or_type>]` locates active meetings by scanning the meetings directory, resolves the target meeting (or prompts when multiple active meetings exist), sets `status: ended` and `ended_at`, and prints a pull-request review reminder.
  - `ot meeting list [--status <status>] [--type <type>] [--json]` lists meetings in a summary table or JSON array, and `Validator` validates meeting `type`, `status`, and `started_at` in `ot check`.


