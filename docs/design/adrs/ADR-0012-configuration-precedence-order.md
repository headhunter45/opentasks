# ADR-0012 - Configuration Precedence Order

Status:
Accepted

Context:

Multiple configuration layers require predictable resolution rules.

Users must be able to determine where a value originates and how to override it.

Decision:

Configuration values shall be resolved in the following order:

1. .ot/config.local.json
2. .ot/config.json
3. ~/.ot/config.json
4. Supported version control commands
5. Environment variables
6. System defaults

Reasoning:

Project-local overrides should take highest priority.

Repository configuration should provide shared project defaults.

User configuration should provide personal defaults.

Automatically discovered values should only be used when explicit configuration is unavailable.

Alternatives Considered:

### User Configuration Before Repository Configuration

Pros:

- Strong user customization

Cons:

- Reduced project consistency

### Environment Variables Before Configuration Files

Pros:

- Familiar to some tools

Cons:

- Difficult to reason about
- Hidden configuration

Consequences:

Positive:

- Deterministic configuration resolution
- Predictable customization
- Easier debugging

Negative:

- Requires documentation
- Requires configuration inspection tooling

## Amendments (As-Built)

- **CLI Flag Overrides**: For settings exposed as CLI options (such as `--width` for output column width or `-C` / `--project-dir` for project root discovery), explicit command-line arguments take precedence above `.ot/config.local.json`.
- **Deep Merging & Per-Field Fallbacks (`src/ot/config.py`)**:
  - JSON configuration files (`DEFAULT_CONFIG` <- `~/.ot/config.json` <- `.ot/config.json` <- `.ot/config.local.json`) are combined via recursive dictionary merge (`deep_merge`).
  - VCS and environment fallbacks are then applied individually for unset `user.name`, `user.email`, and `user.editor` fields.
- **Configuration Inspection Tooling**: CLI commands (`ot config get`, `ot config set`, `ot config list`) are tracked in task `30dc47`.

