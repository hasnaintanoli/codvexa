"""
Route and scan data models for Codvexa.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Route:
    """Represents a single discovered API route."""

    method: str
    path: str
    file: str
    line: Optional[int] = None
    handler: Optional[str] = None
    router: Optional[str] = None
    middlewares: List[str] = field(default_factory=list, compare=False, hash=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert route to a clean dictionary matching the JSON specification."""
        return {
            "method": self.method,
            "path": self.path,
            "file": self.file,
            "line": self.line,
            "handler": self.handler,
            "router": self.router,
        }


@dataclass
class ScanError:
    """Represents an error encountered while scanning or parsing a file."""

    file: str
    reason: str
    line: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file,
            "reason": self.reason,
            "line": self.line,
        }


@dataclass
class ProjectInfo:
    """Information about the scanned project."""

    name: str
    path: Path
    framework: str = "Unknown"
    language: str = "JavaScript / TypeScript"
    has_package_json: bool = False
    has_tsconfig: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": str(self.path),
            "framework": self.framework,
            "language": self.language,
        }


@dataclass
class ScanResult:
    """The aggregate result of scanning a project."""

    project: ProjectInfo
    files_scanned: int = 0
    total_files: int = 0
    skipped_files: int = 0
    routes: List[Route] = field(default_factory=list)
    errors: List[ScanError] = field(default_factory=list)

    @property
    def routes_found(self) -> int:
        return len(self.routes)

    def to_dict(self, codvexa_version: str = "0.1.0") -> Dict[str, Any]:
        """Serialize complete scan results to dictionary conforming to requirements."""
        return {
            "codvexa_version": codvexa_version,
            "project": self.project.name,
            "framework": self.project.framework,
            "files_scanned": self.files_scanned,
            "routes_found": self.routes_found,
            "routes": [r.to_dict() for r in self.routes],
        }
