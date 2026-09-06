#!/usr/bin/env python3
"""Build a UTF-8 skill ZIP from version-controlled runtime files only.

Run after committing release changes: python scripts/build_skill_zip.py
The archive excludes local inputs, generated outputs, caches and Git history.
"""
import json
from pathlib import Path
import subprocess
import zipfile

REPO = Path(__file__).resolve().parent.parent
ROOT_FILES = {"SKILL.md", "README.md", "README_EN.md", "pyproject.toml", "LICENSE",
              "DISCLAIMER.md", "CITATIONS.md", "PROVENANCE.md", "NOTICE.md",
              "CHANGELOG.md", "AGENTS.md", "GEMINI.md", ".gitignore"}
DIRECTORIES = {"calc", "render", "schema", "examples", "tripkit", "docs", "skills", ".claude-plugin"}


def main():
    version = json.loads((REPO / ".claude-plugin/plugin.json").read_text())["version"]
    paths = subprocess.check_output(["git", "-C", str(REPO), "ls-files", "-z"]).decode().split("\0")
    output = REPO / "dist" / f"tw-gov-overseas-trip-kit-skill-v{version}.zip"
    output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(filter(None, paths)):
            if name not in ROOT_FILES and Path(name).parts[0] not in DIRECTORIES:
                continue
            source = REPO / name
            if not source.resolve().is_relative_to(REPO):
                raise ValueError(f"Refusing external symlink: {name}")
            # Read bytes to dereference the kit's internal SKILL aliases portably.
            # ZipFile emits UTF-8 names, including Traditional Chinese guide names.
            archive.writestr(f"tw-gov-overseas-trip-kit/{name}", source.read_bytes())
    print(output)


if __name__ == "__main__":
    main()
