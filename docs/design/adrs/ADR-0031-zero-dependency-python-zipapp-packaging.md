# ADR-0031 - Zero-Dependency Python 3.11+ ZipApp Packaging

Status:
Accepted

Context:

Open Tasks requires project-installed tool versions beneath `.ot/bin/<version>/` (ADR-0009) and a lightweight global launcher (`ot`) or project wrapper (`./oat`) (ADR-0010).

Evaluating packaging approaches (`99-implementation-notes.md`) considered:

- Single Python script
- Standard-library Python `.zipapp`
- PEX archives
- Project-local virtual environments
- Bundled language runtimes

Project-local virtual environments and third-party package installations introduce friction, platform-specific binary issues, network requirements during installation, and large disk footprints.

Decision:

Open Tasks shall target Python 3.11+ using only the Python standard library at runtime, and shall be distributed and installed into projects as a self-contained executable `.zipapp` (`ot.zipapp`) accompanied by a JSON release manifest (`ot-manifest.json`) and SHA-256 checksums (`SHA256SUMS`).

Reasoning:

- Python 3.11+ is widely available across macOS, Linux, and Windows and provides modern typing and `dataclasses`.
- Eliminating third-party runtime dependencies allows a single `.zipapp` (~25 KB) to run on any host with Python 3.11+ without `pip`, virtual environments, or native C extensions.
- Standard `zipapp` archives can be executed directly by the Python interpreter (`python3 ot.zipapp`) and inspected or verified with standard SHA-256 digests.

Alternatives Considered:

### Third-Party Dependencies in a Virtual Environment

Pros:

- Access to external CLI, YAML, and Markdown libraries

Cons:

- Requires per-project or per-version `venv` creation and `pip install`
- Slower installation and harder offline operation

### PyInstaller / Native Binary Per Platform

Pros:

- No host Python required

Cons:

- Large binaries (tens of megabytes per version)
- Requires building and signing separate artifacts for every OS and CPU architecture

Consequences:

Positive:

- Fast, deterministic, cross-platform single-file distribution
- Minimal storage overhead in `~/.ot/versions/` and `.ot/bin/<version>/`
- Trivial offline caching and SHA-256 verification

Negative:

- YAML frontmatter parsing, Markdown parsing, and CLI argument handling must be maintained using the Python standard library
