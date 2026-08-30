"""
Project metadata and framework detection.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from codvexa.models.route import ProjectInfo


def detect_project(project_path: Path, source_files: Optional[List[Path]] = None) -> ProjectInfo:
    """
    Inspect a project directory and extract metadata such as project name,
    primary language, and whether Express framework is present.
    """
    resolved_path = project_path.resolve()
    project_name = resolved_path.name or "project"
    framework = "Unknown"
    has_package_json = False
    has_tsconfig = False

    package_json_path = resolved_path / "package.json"
    tsconfig_path = resolved_path / "tsconfig.json"

    if tsconfig_path.is_file():
        has_tsconfig = True

    if package_json_path.is_file():
        has_package_json = True
        try:
            with open(package_json_path, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # Read name from package.json if available
                    pkg_name = data.get("name")
                    if isinstance(pkg_name, str) and pkg_name.strip():
                        project_name = pkg_name.strip()

                    # Check dependencies for express
                    deps = {
                        **data.get("dependencies", {}),
                        **data.get("devDependencies", {}),
                        **data.get("peerDependencies", {}),
                    }
                    if "express" in deps or "@types/express" in deps:
                        framework = "Express"
        except (json.JSONDecodeError, OSError, TypeError):
            # Gracefully ignore corrupted package.json
            pass

    # Detect language based on discovered files
    has_js = False
    has_ts = False

    if source_files:
        for f in source_files:
            suffix = f.suffix.lower()
            if suffix in {".ts", ".tsx", ".mts", ".cts"}:
                has_ts = True
            elif suffix in {".js", ".jsx", ".mjs", ".cjs"}:
                has_js = True

    if has_js and has_ts:
        language = "JavaScript / TypeScript"
    elif has_ts:
        language = "TypeScript"
    elif has_js:
        language = "JavaScript"
    else:
        language = "TypeScript" if has_tsconfig else "JavaScript / TypeScript"

    return ProjectInfo(
        name=project_name,
        path=resolved_path,
        framework=framework,
        language=language,
        has_package_json=has_package_json,
        has_tsconfig=has_tsconfig,
    )
