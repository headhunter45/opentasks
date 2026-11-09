# ADR-0033 - Attachment Ownership, Relative Markdown Links, And Validation Scope

Status:
Accepted

Context:

Work items and meetings frequently reference supporting artifacts such as screenshots, diagrams, design documents, and external URLs (`02-filesystem-layout.md`, `04-work-item-model.md`, `07-validation-and-repair.md`).

Several open questions (`OQ-0002`, `OQ-0003`, `OQ-0013`, `OQ-0017`) needed resolution:

1. How should attachments be stored and owned on disk?
2. Should attachments require dedicated UUIDs or sidecar metadata files, or be referenced via standard relative Markdown links?
3. What should `ot check` validate regarding links (within `.ot/`, elsewhere in the project root, or external `http(s)://` URLs) and orphaned attachment files?

Decision:

1. **Subfolder Ownership Model**:
   - Local attachments belonging to a WorkItem or Meeting shall be stored inside an `attachments/` directory within that WorkItem's or Meeting's directory subtree:
     - `<WorkItemDir>/attachments/<filename>`
     - `<MeetingDir>/attachments/<filename>`
2. **Relative Markdown Links Without Sidecar Metadata**:
   - Attachments are referenced directly from WorkItem descriptions, comments, and meeting notes using standard relative Markdown links (e.g., `![screenshot](attachments/error.png)` or `[spec](attachments/design.pdf)`).
   - No separate attachment UUID registry or sidecar metadata files are required.
3. **Link & Attachment Validation Scope (`ot check`)**:
   - Validate all relative Markdown links in OT documents (WorkItems and Meetings), including links pointing to local `attachments/` as well as relative links to files elsewhere within the project root (the parent directory of `.ot/`), reporting broken target paths as `ERROR` or `WARNING` diagnostics.
   - Report unreferenced files inside `attachments/` directories as `WARNING` diagnostics (orphaned attachments) without automatically deleting user files during `ot check --fix`.
   - Do **not** perform network requests to validate external `http://` or `https://` URLs, preserving offline and deterministic operation.

Reasoning:

- Standard relative Markdown links render natively in GitHub, GitLab, Obsidian, VS Code, and static site generators without requiring Open Tasks tooling.
- Keeping attachments inside `<OwnerDir>/attachments/` makes work item and meeting directories self-contained and easy to move or archive (consistent with ADR-0026).
- Avoiding network checks during `ot check` preserves fast, deterministic, offline validation (consistent with ADR-0001).

Alternatives Considered:

### Dedicated Attachment UUIDs and Sidecar Metadata Files

Pros:

- Explicit author/timestamp tracking per attachment file

Cons:

- Clutters directories with `.meta.json` sidecar files or bloated YAML frontmatter
- Git history already records who added or modified an attachment and when
- Breaks tool-independent manual file placement

### Network Verification of External URLs

Pros:

- Detects link rot on external websites

Cons:

- Breaks offline operation and sandboxed CI environments
- Introduces flaky, slow validation results

Consequences:

Positive:

- Native rendering in Markdown viewers and code forges
- Self-contained WorkItem and Meeting subtrees
- Fast, offline-safe link and orphan validation

Negative:

- Moving a shared attachment between WorkItems requires updating relative links

## Amendments (As-Built)

- **Relative Markdown Link Validation (`src/ot/validation.py`)**: `Validator._validate_markdown_links_in_text()` validates relative Markdown links in WorkItem bodies, comments, and Meeting notes (stripping fenced/inline code blocks and `#anchor` fragments, skipping external URI schemes without network calls, emitting `ERROR` if a relative link escapes `project_root` or targets a missing `attachments/` file, and `WARNING` if another project-relative target file does not exist; tasks `46cc7b`, `ba1cd2`).
- **Attachment CLI & Orphan Detection (`src/ot/cli.py`, `src/ot/validation.py`)**: Implemented `ot attachment add`, `remove`, `list`, and `show` for WorkItems and Meetings (formatting image links as `![label](attachments/<name>)` and non-image links as `[label](attachments/<name>)`), and added `Validator._validate_orphaned_attachments()` to report unreferenced files in `attachments/` directories as `WARNING` diagnostics without auto-deleting user files during `ot check --fix` (task `ba1cd2`).


