# ADR-0008 - Git Style Short Identifiers

Status:
Accepted

Context:

UUIDs are not practical for daily use.

Users frequently need to:

- View work items
- Reference work items
- Create relationships
- Create dependencies

Typing full UUIDs is undesirable.

Decision:

OT shall expose short identifiers derived from canonical UUIDs.

Displayed identifiers shall be:

- Stable
- Unique within the current project
- Extended as necessary to avoid ambiguity

When users specify identifiers, OT shall accept the shortest unambiguous prefix.

Reasoning:

This mirrors the user experience provided by Git commit hashes.

Alternatives Considered:

### Monotonic Ticket Numbers

Pros:

- Familiar
- Human friendly

Cons:

- Coordination required
- Difficult merging

### User Chosen Identifiers

Pros:

- Flexible

Cons:

- Naming collisions
- Increased validation complexity

### Full UUID Usage

Pros:

- No ambiguity

Cons:

- Poor usability

Consequences:

Positive:

- Human friendly references
- Merge friendliness
- Distributed operation

Negative:

- Requires ambiguity detection
- Requires identifier resolution logic

## Amendments (As-Built)

- **Short ID Derivation & Length Rules (`src/ot/identifiers.py`)**:
  - Short identifiers are derived directly from the canonical UUID with hyphens stripped and lowercased (`clean_hex`).
  - The default display length is **6 hex characters** (`DEFAULT_SHORT_ID_LENGTH = 6`), automatically extended character-by-character as needed until unique across all WorkItems in the repository (`compute_short_id`).
  - When resolving user-supplied hex prefixes (`resolve_identifier`), the minimum accepted prefix length is **4 hex characters** (`MIN_SHORT_ID_LENGTH = 4`).
- **Resolution Precedence**: `resolve_identifier` resolves user queries in the following order:
  1. Exact full UUID match (case-insensitive).
  2. Unambiguous hex prefix match (`>= 4` hex chars after stripping hyphens); raises `AmbiguousIdentifierError` if multiple items match.
  3. Exact case-insensitive WorkItem `title` match; raises `AmbiguousIdentifierError` if multiple items share the same title.

