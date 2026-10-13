"""Stage the source needed for a portable UV-backed MCP Bundle."""
from __future__ import annotations

import json
import shutil
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "build" / "mcpb"


def main() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "mcpb" / "manifest.json").read_text(encoding="utf-8"))
    if manifest["version"] != project["project"]["version"]:
        raise SystemExit("MCPB manifest and project versions differ")

    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    for name in ("pyproject.toml", "README.md", "LICENSE"):
        shutil.copy2(ROOT / name, STAGE / name)
    for name in ("mcp_trace", "agenthawk"):
        shutil.copytree(
            ROOT / "src" / name,
            STAGE / "src" / name,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    shutil.copy2(ROOT / "mcpb" / "manifest.json", STAGE / "manifest.json")
    print(STAGE)


if __name__ == "__main__":
    main()
