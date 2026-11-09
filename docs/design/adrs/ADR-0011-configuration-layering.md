# ADR-0011 - Configuration Layering

Status:
Accepted

Context:

OT requires configuration values that apply at different scopes.

Examples include:

- User identity
- Preferred editor
- Work item types
- Work item statuses
- Templates
- Upgrade behavior

Some values belong to a project while others belong to individual users.

Decision:

OT shall support multiple configuration layers.

The initial configuration layers are:

- Project configuration
- Project-local user overrides
- Global user configuration

Configuration is resolved according to a defined precedence order.

Reasoning:

Projects require shared defaults while individual users require local customization.

Separating these concerns reduces repository noise and prevents user-specific settings from leaking into source control.

Alternatives Considered:

### Single Configuration File

Pros:

- Simple implementation

Cons:

- User preferences leak into repositories
- Difficult team collaboration

### Global Configuration Only

Pros:

- Simple management

Cons:

- No project-specific configuration

### Repository Configuration Only

Pros:

- Consistent project behavior

Cons:

- User preferences become repository data

Consequences:

Positive:

- Clean separation of concerns
- Reduced repository churn
- Better team experience

Negative:

- Additional lookup logic
- Additional validation requirements

## Amendments (As-Built)

- **Implemented Layering (`src/ot/config.py`)**: `load_config` merges `DEFAULT_CONFIG`, `~/.ot/config.json`, `.ot/config.json`, and `.ot/config.local.json` with VCS and environment fallbacks.
- **Deferred / Partial Scope**:
  - CLI commands for inspecting and modifying configuration layers (`ot config get`, `ot config set`, `ot config list`) are tracked in task `30dc47`.

