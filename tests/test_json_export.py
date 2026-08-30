import json
from pathlib import Path

from codvexa import __version__
from codvexa.exporters.json_export import export_to_json_file, export_to_json_string
from codvexa.models.route import ProjectInfo, Route, ScanResult


def test_json_export_string():
    project = ProjectInfo(
        name="my-api",
        path=Path("/tmp/my-api"),
        framework="Express",
        language="JavaScript / TypeScript",
    )
    routes = [
        Route(
            method="GET",
            path="/users",
            file="routes/users.js",
            line=12,
            handler="getUsers",
            router="router",
        ),
        Route(
            method="POST",
            path="/users",
            file="routes/users.js",
            line=28,
            handler="createUser",
            router="router",
        ),
    ]
    scan_result = ScanResult(
        project=project,
        files_scanned=42,
        total_files=50,
        skipped_files=8,
        routes=routes,
    )

    json_str = export_to_json_string(scan_result)
    data = json.loads(json_str)

    assert data["codvexa_version"] == __version__
    assert data["project"] == "my-api"
    assert data["framework"] == "Express"
    assert data["files_scanned"] == 42
    assert data["routes_found"] == 2
    assert len(data["routes"]) == 2

    assert data["routes"][0] == {
        "method": "GET",
        "path": "/users",
        "file": "routes/users.js",
        "line": 12,
        "handler": "getUsers",
        "router": "router",
    }


def test_json_export_file(tmp_path: Path):
    project = ProjectInfo(
        name="test-project",
        path=tmp_path,
        framework="Express",
    )
    routes = [
        Route(
            method="DELETE",
            path="/items/:id",
            file="routes/items.js",
            line=40,
            handler="deleteItem",
            router="itemsRouter",
        )
    ]
    scan_result = ScanResult(
        project=project,
        files_scanned=5,
        total_files=5,
        routes=routes,
    )

    out_file = tmp_path / "sub" / "routes.json"
    export_to_json_file(scan_result, out_file)

    assert out_file.is_file()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["project"] == "test-project"
    assert len(data["routes"]) == 1
    assert data["routes"][0]["method"] == "DELETE"
