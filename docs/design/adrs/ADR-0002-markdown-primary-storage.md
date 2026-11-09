# ADR-0002 - Markdown as Primary Storage Format

Status:
Accepted

Context:

OT requires a storage format for user-editable information such as:

- Work item descriptions
- Meeting notes
- Planning artifacts
- Comments

The format should be easy for both humans and tools to consume.

Decision:

Use Markdown as the primary storage format for user-editable content.

Reasoning:

Markdown is:

- Human readable
- Plain text
- Widely supported
- Easy to review in pull requests
- Easy to search
- Easy to edit manually
- Compatible with GitHub
- Compatible with GitLab
- Compatible with Obsidian

Users should be able to inspect and modify project data without requiring OT.

Alternatives Considered:

### JSON

Pros:

- Structured
- Easy to parse

Cons:

- Poor long-form authoring experience
- Difficult manual editing

### YAML

Pros:

- Human readable
- Structured

Cons:

- Error-prone indentation
- Less friendly for long-form content

### Database Storage

Pros:

- Structured
- Efficient queries

Cons:

- Not directly editable
- Requires tooling

Consequences:

Positive:

- Easy review process
- Tool independence
- Human-readable history
- Strong ecosystem support

Negative:

- Requires validation
- Requires parsing conventions
- Some structured data may require frontmatter or metadata blocks

## Amendments (As-Built)

- **YAML Frontmatter Schema**: Work item metadata (`id`, `title`, `type`, `status`, `size`, `created_at`, `updated_at`, `parent`, `author`, `dependencies`, `tags`, plus arbitrary custom fields) is stored in a `---` delimited YAML frontmatter block at the top of each `index.md` file (`src/ot/parser.py`).
- **Zero External Dependencies**: To keep `ot` self-contained inside a standard-library Python `.zipapp`, YAML frontmatter and Markdown sections are parsed and serialized using a lightweight built-in round-trip parser rather than third-party YAML or Markdown packages, preserving unknown user-authored headings and custom frontmatter keys.
- **Comments Section Structure**: Work item comments are stored in a top-level `## Comments` section at the end of the Markdown document, with each comment formatted under `### Comment by <Name> <<Email>> on <ISO-8601-Timestamp>` followed by an HTML comment `<!-- comment-id: <UUID> -->` and the comment body.

