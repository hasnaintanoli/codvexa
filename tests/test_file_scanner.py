"""
Tests for file discovery and project scanner.
"""

import json
from pathlib import Path

from codvexa.scanner.files import discover_files, is_supported_source_file
from codvexa.scanner.project import detect_project


def test_supported_extensions():
    assert is_supported_source_file(Path("app.js"))
    assert is_supported_source_file(Path("app.jsx"))
    assert is_supported_source_file(Path("server.ts"))
    assert is_supported_source_file(Path("component.tsx"))
    assert is_supported_source_file(Path("module.mjs"))
    assert is_supported_source_file(Path("common.cjs"))
    assert not is_supported_source_file(Path("styles.css"))
    assert not is_supported_source_file(Path("index.html"))
    assert not is_supported_source_file(Path("README.md"))
    assert not is_supported_source_file(Path("package.json"))


def test_discover_files_in_temp_dir(tmp_path: Path):
    # Setup test directory structure
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "index.js").write_text("console.log(1);")
    (tmp_path / "src" / "utils.ts").write_text("export const x = 1;")
    (tmp_path / "src" / "style.css").write_text("body { color: red; }")

    # Ignored directory
    (tmp_path / "node_modules" / "express").mkdir(parents=True)
    (tmp_path / "node_modules" / "express" / "index.js").write_text("module.exports = {};")

    # Git directory
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config.js").write_text("// dummy")

    discovered = discover_files(tmp_path)

    # Source files should only contain src/index.js and src/utils.ts
    source_names = {f.name for f in discovered.source_files}
    assert "index.js" in source_names
    assert "utils.ts" in source_names
    assert len(discovered.source_files) == 2

    # node_modules and .git files should not be scanned
    assert not any("node_modules" in str(p) for p in discovered.source_files)
    assert not any(".git" in str(p) for p in discovered.source_files)


def test_discover_single_file(tmp_path: Path):
    single_file = tmp_path / "app.js"
    single_file.write_text("const x = 10;")

    discovered = discover_files(single_file)
    assert len(discovered.source_files) == 1
    assert discovered.source_files[0].name == "app.js"
    assert discovered.total_files == 1


def test_discover_empty_directory(tmp_path: Path):
    empty_dir = tmp_path / "empty_proj"
    empty_dir.mkdir()

    discovered = discover_files(empty_dir)
    assert len(discovered.source_files) == 0
    assert discovered.total_files == 0
    assert discovered.skipped_files == 0


def test_project_detection_with_express(tmp_path: Path):
    pkg = {
        "name": "my-express-api",
        "dependencies": {
            "express": "^4.19.2"
        }
    }
    (tmp_path / "package.json").write_text(json.dumps(pkg))
    (tmp_path / "app.js").write_text("const app = require('express')();")

    info = detect_project(tmp_path, [tmp_path / "app.js"])
    assert info.name == "my-express-api"
    assert info.framework == "Express"
    assert info.language == "JavaScript"
    assert info.has_package_json is True


def test_project_detection_with_typescript(tmp_path: Path):
    (tmp_path / "tsconfig.json").write_text("{}")
    (tmp_path / "server.ts").write_text("import express from 'express';")

    info = detect_project(tmp_path, [tmp_path / "server.ts"])
    assert info.framework == "Unknown"
    assert info.language == "TypeScript"
    assert info.has_tsconfig is True


def test_project_detection_mixed_language(tmp_path: Path):
    info = detect_project(tmp_path, [tmp_path / "app.js", tmp_path / "server.ts"])
    assert info.language == "JavaScript / TypeScript"
