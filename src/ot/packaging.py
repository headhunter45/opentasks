"""Packaging and release artifact build system for Open Tasks."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Dict, List, Optional
import zipapp
import zipfile

from ot.version import is_valid_version


def compute_sha256(file_path: Path | str) -> str:
    """Compute SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class ReleaseManifest:
    """Manifest describing a packaged Open Tasks release artifact."""

    version: str
    build_date: str
    sha256: str
    schema_version: int = 1
    artifact_name: str = "ot.zipapp"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "build_date": self.build_date,
            "sha256": self.sha256,
            "schema_version": self.schema_version,
            "artifact_name": self.artifact_name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ReleaseManifest:
        return cls(
            version=str(data["version"]),
            build_date=str(data.get("build_date", "")),
            sha256=str(data.get("sha256", "")),
            schema_version=int(data.get("schema_version", 1)),
            artifact_name=str(data.get("artifact_name", "ot.zipapp")),
        )


def build_zipapp_artifact(
    src_dir: Path | str,
    output_path: Path | str,
    version: str,
    main_func: str = "ot.launcher:run_launcher",
) -> ReleaseManifest:
    """Package the `ot` source into a self-contained executable ZipApp (.zipapp).

    Generates manifest.json with SHA-256 checksum and version metadata.
    """
    if not is_valid_version(version):
        raise ValueError(f"Cannot package invalid release version: '{version}'")

    src = Path(src_dir).resolve()
    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as staging_dir:
        staging = Path(staging_dir)

        # Copy the ot package into staging
        ot_src = src / "ot"
        if not ot_src.is_dir():
            raise FileNotFoundError(f"Source package not found at {ot_src}")

        import shutil
        shutil.copytree(ot_src, staging / "ot")

        # Inject packaging version into staging __init__.py so artifact reflects release version
        init_py = staging / "ot" / "__init__.py"
        if init_py.is_file():
            import re
            content = init_py.read_text(encoding="utf-8")
            if re.search(r"^__version__\s*=", content, re.MULTILINE):
                content = re.sub(
                    r"^__version__\s*=.*$",
                    f'__version__ = "{version}"',
                    content,
                    flags=re.MULTILINE,
                )
            else:
                content += f'\n__version__ = "{version}"\n'
            init_py.write_text(content, encoding="utf-8")

        # Create __main__.py entry point
        mod_name, func_name = main_func.split(":", 1)
        main_py = staging / "__main__.py"
        main_py.write_text(
            f'import sys\nfrom {mod_name} import {func_name}\n\nif __name__ == "__main__":\n    sys.exit({func_name}())\n',
            encoding="utf-8",
        )

        # Create zipapp archive with shebang
        zipapp.create_archive(
            staging,
            target=out,
            interpreter="/usr/bin/env python3",
            main=None,  # We created __main__.py
        )

    # Compute SHA-256 checksum
    checksum = compute_sha256(out)
    from ot.models import now_iso

    manifest = ReleaseManifest(
        version=version,
        build_date=now_iso(),
        sha256=checksum,
        artifact_name=out.name,
    )

    # Write manifest alongside artifact
    manifest_path = out.parent / f"{out.stem}-manifest.json"
    manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")

    return manifest


def main(args: Optional[List[str]] = None) -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Package Open Tasks release artifact")
    parser.add_argument("--version", "-v", required=True, help="Release version (e.g. 0.1.0)")
    parser.add_argument("--src-dir", "-s", default="src", help="Source directory containing ot/ package")
    parser.add_argument("--output-dir", "-o", default="dist", help="Output directory for packaged release")
    parser.add_argument("--artifact-name", default="ot.zipapp", help="Output artifact filename")

    parsed = parser.parse_args(args)

    out_file = Path(parsed.output_dir) / parsed.artifact_name
    try:
        manifest = build_zipapp_artifact(
            src_dir=parsed.src_dir,
            output_path=out_file,
            version=parsed.version,
        )
        print(f"Successfully packaged Open Tasks v{manifest.version}")
        print(f"Artifact: {out_file}")
        print(f"SHA-256:  {manifest.sha256}")
        return 0
    except Exception as e:
        print(f"Packaging failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

