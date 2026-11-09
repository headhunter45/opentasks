# ADR-0013 - Project and User Configuration Separation

Status:
Accepted

Context:

Some configuration is intended to be shared by all contributors.

Other configuration only applies to a specific user or checkout.

Examples:

Project Configuration:

- Work item types
- Status values
- Size values
- Templates
- System metadata

User Configuration:

- User name
- User email
- Preferred editor

Decision:

Store project and user configuration separately.

Project configuration:

- .ot/config.json

Project-local user overrides:

- .ot/config.local.json

Global user configuration:

- ~/.ot/config.json

Reasoning:

Project data should be reviewable and versioned.

User preferences should remain local.

Alternatives Considered:

### Single Shared Configuration

Pros:

- Simpler structure

Cons:

- User settings leak into source control

### Global User Configuration Only

Pros:

- Simpler local management

Cons:

- Impossible to customize behavior per checkout

Consequences:

Positive:

- Cleaner repositories
- Improved collaboration
- More flexible configuration

Negative:

- Multiple configuration files
- Additional migration considerations

## Amendments (As-Built)

- **Implemented Configuration Structure (`src/ot/config.py`)**:
  - `system`: `configSchemaVersion` (currently `1`) and `toolVersion` (configured semantic version of Open Tasks).
  - `project`: `name` and `description`.
  - `user`: `name`, `email`, `editor`, and optional `outputWidth` (also accepted via `output.width`).
  - `workItem`: `types`, `statuses`, and `sizes` dictionaries mapping keys to `{"label": ..., "description": ...}`.
  - `meeting`: `types` dictionary (`grooming`, `planning`, `retrospective`, `ideation`).
- **User Home Override**: Global user storage defaults to `~/.ot/` and can be redirected via the `OT_USER_HOME` environment variable (falling back to `/tmp/ot-user-<uid>` if `~/.ot` is not writable in sandboxed/CI environments, `src/ot/cache.py`).

