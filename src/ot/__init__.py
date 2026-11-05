"""Open Tasks (ot) core package."""

# Last-resort version, used only when git cannot be consulted (a bare,
# build-injected .zipapp with no .git tree beside it). Normal source
# checkouts and builds resolve the *real* version from the most recent
# ancestor tag, matching .github/workflows/deploy.yml and scripts/build-release.
__version__ = "0.1.0"

try:
    import subprocess
    from pathlib import Path

    _git_dir = Path(__file__).resolve().parent.parent.parent / ".git"
    if _git_dir.exists():
        # Nearest (most recent) ancestor tag, e.g. "v0.1.2-dev" off a dev
        # HEAD. Mirrors the release pipeline's version resolution.
        _res = subprocess.run(
             ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            timeout=1,
         )
        if _res.returncode == 0:
            _tag = _res.stdout.strip().lstrip("v")
            if _tag:
                 __version__ = _tag
except Exception:
    pass
