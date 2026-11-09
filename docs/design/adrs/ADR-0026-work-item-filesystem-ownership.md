# ADR-0026 - Work Item Filesystem Ownership

Status:
Accepted

Context:

Work items may contain:

- Child work items
- Attachments
- Additional generated content
- Future metadata

The filesystem layout must support hierarchical organization while remaining understandable to users.

Decision:

Each work item owns a subtree of the filesystem.

Files and folders associated with a work item should be stored within that work item's subtree.

Reasoning:

A work item represents a logical unit of work.

Keeping related content together improves:

- Discoverability
- Validation
- Refactoring
- Portability

Alternatives Considered:

### Flat Filesystem

Pros:

- Simple layout

Cons:

- Difficult attachment organization
- Difficult nesting

### Central Attachment Storage

Pros:

- Easier deduplication

Cons:

- Weaker ownership model
- Harder navigation

Consequences:

Positive:

- Clear ownership boundaries
- Natural hierarchy
- Easier validation

Negative:

- Filesystem layout rules become more important

Open Questions:

- Final directory structure
- Attachment placement rules
- Child work item representation

## Amendments (As-Built)

- **Promoted from `Proposed` to `Accepted`**: The directory-per-WorkItem layout is implemented in `src/ot/cli.py`, `src/ot/parser.py`, and `src/ot/scanner.py`.
- **WorkItem Directory & Primary Document**:
  - Each WorkItem owns a directory named `<PascalCaseSanitizedTitle>/` (generated from up to the first 6 alphanumeric words of the title via `sanitize_folder_name`, or `Task-<short_id>` if untitled) containing `index.md` as its primary document.
  - `read_work_item` and `write_work_item` accept either a directory path (resolving `<dir>/index.md`) or a direct `.md` file path, and `RepositoryScanner.scan_tasks_directory` recursively indexes all `.md` files containing a valid `id` beneath `.ot/tasks/`.
- **Child WorkItem Representation**:
  - When a WorkItem is created with `--parent <parent>`, its directory is placed directly inside the parent WorkItem's directory (`.ot/tasks/<ParentFolder>/<ChildFolder>/index.md`) alongside setting `parent: <parent_uuid>` in YAML frontmatter.
- **Attachments**:
  - Dedicated attachment CLI subcommands (`ot attachment ...`) are not yet implemented; attachments placed within a WorkItem's directory subtree remain co-located with that WorkItem.

