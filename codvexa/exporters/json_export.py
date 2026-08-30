"""
JSON export functionality for Codvexa scan results.
"""

from __future__ import annotations

import json
from pathlib import Path

from codvexa import __version__
from codvexa.models.route import ScanResult


def export_to_json_string(scan_result: ScanResult, indent: int = 2) -> str:
    """
    Serialize a ScanResult object to a formatted JSON string.

    Args:
        scan_result: The scan result to serialize.
        indent: Indentation level for pretty printing (default 2).

    Returns:
        JSON string representation with UTF-8 support.
    """
    data = scan_result.to_dict(codvexa_version=__version__)
    return json.dumps(data, indent=indent, ensure_ascii=False)


def export_to_json_file(scan_result: ScanResult, output_path: Path, indent: int = 2) -> None:
    """
    Write a ScanResult to a JSON file on disk.

    Args:
        scan_result: The scan result to write.
        output_path: Target path for the JSON file.
        indent: Indentation level (default 2).

    Raises:
        OSError: If writing to the file fails.
    """
    json_content = export_to_json_string(scan_result, indent=indent)
    target = output_path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(json_content + "\n")
