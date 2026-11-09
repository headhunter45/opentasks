# ADR-0009 - Project Installed Tool Versions

Status:
Accepted

Context:

Projects may require different OT versions.

A user's globally installed OT version may not match the version expected by all projects.

Decision:

Projects shall install their configured OT implementation under:

.ot/bin

The globally installed OT executable is a wrapper responsible for locating and invoking the expected project version.

Reasoning:

Projects should remain independent of user workstation upgrades.

Alternatives Considered:

### Single Global Installation

Pros:

- Simple deployment

Cons:

- Difficult upgrades
- Project incompatibility

### Python Package Per Project

Pros:

- Strong isolation

Cons:

- High storage overhead
- Additional virtual environments

### Bundled Runtime Per Project

Pros:

- Full isolation

Cons:

- Significant duplication
- Large project footprint

Consequences:

Positive:

- Version consistency
- Repeatable project behavior
- Reduced upgrade risk

Negative:

- Multiple copies of OT may exist
- Upgrade logic required

## Amendments (As-Built)

- **Versioned Subdirectory Layout**: Project-installed binaries are stored in versioned subdirectories under `.ot/bin/<version>/ot.zipapp` alongside `.ot/bin/<version>/ot-manifest.json` (`src/ot/upgrade.py`, `src/ot/installation.py`, `src/ot/launcher.py`), allowing multiple versions to coexist during upgrades or branch switches while retaining backward-compatible fallback lookup for legacy flat `.ot/bin/ot.zipapp` layouts.
- **Configured Version Key**: The project's expected tool version is recorded at `system.toolVersion` in `.ot/config.json`.
- **Automatic Download & User Version Cache**: When the launcher (`run_launcher` / `ensure_project_binary` in `src/ot/launcher.py`) or project wrapper (`oat`) runs in a project whose configured `system.toolVersion` is not yet installed under `.ot/bin/<version>/`, it checks the shared user cache (`~/.ot/versions/<version>/ot.zipapp`, or `$OT_USER_HOME/versions/<version>/ot.zipapp`), downloads the release `.zipapp` and verifies its SHA-256 against `SHA256SUMS` from GitHub Releases if not cached (`src/ot/cache.py`), and populates `.ot/bin/<version>/`.
- **Git Ignore Management**: `ot init` automatically ensures `.ot/bin/` is added to the project's `.gitignore` (`_ensure_gitignore_entry` in `src/ot/installation.py`) so binary artifacts are not committed to source control.

