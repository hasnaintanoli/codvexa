"""
CLI interaction tests using Typer CliRunner.
"""

import json
from pathlib import Path
from typer.testing import CliRunner

from codvexa.cli import app

runner = CliRunner()
SAMPLE_API_DIR = Path(__file__).parent.parent / "examples" / "sample-api"


def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "Codvexa v0.1.0" in result.stdout


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Codvexa" in result.stdout
    assert "scan" in result.stdout


def test_cli_scan_sample_api():
    result = runner.invoke(app, ["scan", str(SAMPLE_API_DIR)])
    assert result.exit_code == 0
    assert "Codvexa v0.1.0" in result.stdout
    assert "API routes found:" in result.stdout
    assert "GET" in result.stdout
    assert "/health" in result.stdout
    assert "/api/users/" in result.stdout or "/api/users" in result.stdout
    assert "Scan completed successfully." in result.stdout


def test_cli_scan_json_output():
    result = runner.invoke(app, ["scan", str(SAMPLE_API_DIR), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["codvexa_version"] == "0.1.0"
    assert data["project"] == "sample-api"
    assert data["framework"] == "Express"
    assert data["routes_found"] > 0
    paths = [r["path"] for r in data["routes"]]
    assert "/health" in paths


def test_cli_scan_output_file(tmp_path: Path):
    out_file = tmp_path / "discovered.json"
    result = runner.invoke(app, ["scan", str(SAMPLE_API_DIR), "--output", str(out_file)])
    assert result.exit_code == 0
    assert out_file.is_file()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["project"] == "sample-api"


def test_cli_scan_nonexistent_path():
    result = runner.invoke(app, ["scan", "/non/existent/path/here"])
    assert result.exit_code == 1
