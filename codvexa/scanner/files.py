"""
File discovery and traversal for JavaScript and TypeScript projects.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set, Tuple

# Supported source file extensions
SUPPORTED_EXTENSIONS = {
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".mts",
    ".cts",
}

# Directories to ignore during scanning
IGNORED_DIRECTORIES = {
    "node_modules",
    ".git",
    ".next",
    ".nuxt",
    ".turbo",
    ".output",
    ".cache",
    ".vscode",
    ".idea",
    "dist",
    "build",
    "out",
    "coverage",
    "venv",
    ".venv",
    "env",
    ".env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".yarn",
    ".pnpm-store",
    "tmp",
    "temp",
    ".svn",
    ".hg",
}


@dataclass
class DiscoveredFiles:
    """Statistics and lists of discovered files."""

    source_files: List[Path] = field(default_factory=list)
    total_files: int = 0
    skipped_files: int = 0
    failed_files: List[Tuple[Path, str]] = field(default_factory=list)


def is_supported_source_file(path: Path) -> bool:
    """Check whether a given path is a supported JS/TS source file."""
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def discover_files(
    root_path: Path,
    custom_ignored_dirs: Set[str] | None = None,
) -> DiscoveredFiles:
    """
    Recursively discover all JavaScript and TypeScript source files in root_path.

    Safely traverses directories, skipping known build/dependency folders and
    handling unreadable files or permission errors gracefully.
    """
    ignored = IGNORED_DIRECTORIES if custom_ignored_dirs is None else (IGNORED_DIRECTORIES | custom_ignored_dirs)
    result = DiscoveredFiles()

    root_path = root_path.resolve()

    # If the user supplied a single file directly
    if root_path.is_file():
        result.total_files = 1
        if is_supported_source_file(root_path):
            result.source_files.append(root_path)
        else:
            result.skipped_files = 1
        return result

    if not root_path.is_dir():
        return result

    for current_root, dirs, files in os.walk(root_path, topdown=True, followlinks=False):
        # Filter directories in-place to avoid descending into ignored directories
        dirs[:] = [
            d for d in dirs
            if d not in ignored and not d.startswith(".")
        ]

        for file_name in files:
            result.total_files += 1
            file_path = Path(current_root) / file_name

            try:
                if is_supported_source_file(file_path):
                    result.source_files.append(file_path)
                else:
                    result.skipped_files += 1
            except (OSError, PermissionError) as exc:
                result.failed_files.append((file_path, str(exc)))
                result.skipped_files += 1

    return result
