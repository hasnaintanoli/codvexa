"""
Project and file scanner module.
"""

from codvexa.scanner.files import (
    IGNORED_DIRECTORIES,
    SUPPORTED_EXTENSIONS,
    DiscoveredFiles,
    discover_files,
    is_supported_source_file,
)
from codvexa.scanner.project import detect_project

__all__ = [
    "IGNORED_DIRECTORIES",
    "SUPPORTED_EXTENSIONS",
    "DiscoveredFiles",
    "discover_files",
    "is_supported_source_file",
    "detect_project",
]
