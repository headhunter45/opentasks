# ADR-0032 - YAML Frontmatter And Unidirectional Relationship Storage

Status:
Accepted

Context:

Work items require machine-readable metadata and explicit parent-child and dependency relationships (`04-work-item-model.md`, `OQ-0009`, `99-implementation-notes.md`).

Two key design questions arose:

1. How should structured metadata be embedded in Markdown work item files (YAML frontmatter, JSON frontmatter, or Markdown metadata tables)?
2. Should relationships (`parent`/`children`, `dependencies`/`blocks`) be stored unidirectionally on one WorkItem or bidirectionally in both WorkItems' files?

Decision:

1. Store WorkItem metadata in a `---` delimited YAML frontmatter block at the top of each WorkItem's `index.md` file.
2. Store relationships **unidirectionally** in the YAML frontmatter of the child or dependent WorkItem:
   - `parent`: canonical UUID of the parent WorkItem (stored only on the child).
   - `dependencies`: list of canonical UUIDs of WorkItems that this item depends on (stored only on the dependent item).
3. Compute inverse relationships (`children` and `dependents` / `blocks`) dynamically in memory when scanning the repository (`WorkItemIndex` in `src/ot/scanner.py`).

Reasoning:

- YAML frontmatter is the de facto standard across GitHub, GitLab, Obsidian, and static site generators, keeping files human-readable while separating metadata from narrative Markdown body content.
- Unidirectional relationship storage means adding a child task or adding a dependency only modifies **one** file (`child.md`), eliminating two-file synchronization issues, merge conflicts on popular parent Epics, and bidirectional inconsistency errors.

Alternatives Considered:

### Bidirectional Relationship Storage

Pros:

- Inspecting raw frontmatter of a parent shows all children without scanning

Cons:

- Creating a child task or dependency modifies two files simultaneously
- High risk of Git merge conflicts on parent Epics when multiple contributors add subtasks on branches
- Requires repair logic whenever the two sides drift out of sync

### JSON Frontmatter

Pros:

- Native `json` module in Python standard library

Cons:

- Less ergonomic for humans to edit manually due to strict braces, quotes, and trailing comma rules

Consequences:

Positive:

- Single-file edits when creating subtasks or dependencies
- Branch- and merge-friendly relationship changes
- Zero bidirectional drift between parent and child files

Negative:

- Discovering a WorkItem's children or dependents requires indexing `.ot/tasks/` (`WorkItemIndex`)
