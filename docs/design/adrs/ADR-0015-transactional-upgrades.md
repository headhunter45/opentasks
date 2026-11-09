# ADR-0015 - Transactional Upgrades

Status:
Accepted

Context:

OT upgrades may involve:

- Tool version changes
- Configuration migrations
- Template updates
- Filesystem layout changes

Failed upgrades must not leave projects in an inconsistent state.

Decision:

OT upgrades shall be transactional.

Upgrade activities shall occur in a temporary location until validation succeeds.

The existing installation remains unchanged until completion of the upgrade.

Reasoning:

Partially applied upgrades create difficult recovery scenarios and can corrupt project state.

Alternatives Considered:

### In-Place Upgrades

Pros:

- Simpler implementation

Cons:

- Risk of partial upgrades
- Difficult rollback

### Automatic Rollback

Pros:

- Better recovery

Cons:

- Additional complexity
- More failure modes

Consequences:

Positive:

- Safe upgrades
- Deterministic behavior
- Easier recovery

Negative:

- Increased implementation complexity
- Additional temporary storage requirements

## Amendments (As-Built)

- **Implemented Staging & Commit Flow (`perform_transactional_upgrade` in `src/ot/upgrade.py`)**:
  1. Validates that the target version is a valid semantic version and is greater than the current project version (downgrades raise `UpgradeError`; same-version returns `already_up_to_date`).
  2. Resolves and verifies the target `.zipapp` artifact via local cache (`~/.ot/versions/<version>/`), optional `--mirror` / `OT_MIRROR_DIR`, GitHub Releases (`SHA256SUMS`), or local source build fallback.
  3. Supports `--dry-run` to verify artifact availability without modifying the project.
  4. Copies `.ot/` into a `tempfile.TemporaryDirectory()` staging workspace, updates `system.toolVersion` in the staged `config.json`, installs `.ot/bin/<target_version>/ot.zipapp` + `ot-manifest.json`, installs any new default templates (`overwrite=False`), and runs `Validator(staging).validate_all()`.
  5. Only if zero `Severity.ERROR` diagnostics occur in staging are changes committed to the real `.ot/` directory, preserving any older `.ot/bin/<old_version>/` directories, refreshing `oat` / `oat.bat`, and removing legacy `otw` / `otw.bat` scripts.
- **Deferred / Partial Scope**:
  - Multi-version configuration schema migration steps and modified-template merge/migration handling during upgrades are tracked in task `e04754`.

