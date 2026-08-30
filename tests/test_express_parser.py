"""
Tests for Tree-sitter Express route parsing and prefix resolution.
"""

from pathlib import Path

from codvexa.parser.express import (
    combine_paths,
    parse_express_routes,
    parse_project_routes,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_combine_paths():
    assert combine_paths("/api", "/users") == "/api/users"
    assert combine_paths("/api/users", "/") == "/api/users/"
    assert combine_paths("/api/users", "/:id") == "/api/users/:id"
    assert combine_paths("/", "/health") == "/health"
    assert combine_paths("", "/health") == "/health"
    assert combine_paths("/api", "") == "/api"
    assert combine_paths("api", "users") == "/api/users"


def test_basic_express_routes():
    code = (FIXTURES_DIR / "basic_express.js").read_text(encoding="utf-8")
    routes = parse_express_routes(code, "basic_express.js")

    route_map = {(r.method, r.path): r for r in routes}

    assert ("GET", "/users") in route_map
    assert route_map[("GET", "/users")].handler == "getUsers"
    assert route_map[("GET", "/users")].line == 24

    assert ("POST", "/users") in route_map
    assert route_map[("POST", "/users")].handler == "createUser"

    assert ("PUT", "/users/:id") in route_map
    assert route_map[("PUT", "/users/:id")].handler == "updateUser"

    assert ("PATCH", "/users/:id") in route_map
    assert route_map[("PATCH", "/users/:id")].handler == "patchUser"

    assert ("DELETE", "/users/:id") in route_map
    assert route_map[("DELETE", "/users/:id")].handler == "deleteUser"

    assert ("OPTIONS", "/users") in route_map
    assert route_map[("OPTIONS", "/users")].handler == "<anonymous>"

    assert ("HEAD", "/users") in route_map
    assert ("ALL", "/status") in route_map


def test_router_with_middlewares_and_chaining():
    code = (FIXTURES_DIR / "router_example.js").read_text(encoding="utf-8")
    routes = parse_express_routes(code, "router_example.js")

    route_map = {(r.method, r.path): r for r in routes}

    # Direct routes
    assert ("GET", "/") in route_map
    assert route_map[("GET", "/")].handler == "listProducts"

    assert ("POST", "/") in route_map
    assert route_map[("POST", "/")].handler == "createProduct"
    assert route_map[("POST", "/")].middlewares == ["authenticate", "authorize"]

    # Chained .route('/:id')
    assert ("GET", "/:id") in route_map
    assert ("PUT", "/:id") in route_map
    assert ("DELETE", "/:id") in route_map


def test_typescript_routes():
    code = (FIXTURES_DIR / "typescript_example.ts").read_text(encoding="utf-8")
    routes = parse_express_routes(code, "typescript_example.ts")

    methods = {r.method for r in routes}
    paths = {r.path for r in routes}

    assert "GET" in methods
    assert "POST" in methods
    assert "DELETE" in methods
    assert "/items" in paths
    assert "/items/:id" in paths


def test_invalid_syntax_graceful_recovery():
    code = (FIXTURES_DIR / "invalid.js").read_text(encoding="utf-8")
    routes = parse_express_routes(code, "invalid.js")

    # Parser should not crash and still recover valid routes if AST allows
    assert isinstance(routes, list)
    valid_paths = [r.path for r in routes]
    assert "/valid-in-broken" in valid_paths


def test_project_route_mount_prefix_resolution(tmp_path: Path):
    app_js = """
    const express = require('express');
    const app = express();
    const usersRouter = require('./routes/users');

    app.get('/health', (req, res) => res.send('ok'));
    app.use('/api/v1/users', usersRouter);
    """

    users_js = """
    const express = require('express');
    const router = express.Router();

    router.get('/', (req, res) => res.json([]));
    router.get('/:id', (req, res) => res.json({}));
    router.post('/', (req, res) => res.json({}));

    module.exports = router;
    """

    (tmp_path / "routes").mkdir()
    (tmp_path / "app.js").write_text(app_js)
    (tmp_path / "routes" / "users.js").write_text(users_js)

    files = [tmp_path / "app.js", tmp_path / "routes" / "users.js"]
    routes, errors = parse_project_routes(files, tmp_path)

    assert len(errors) == 0
    route_paths = {(r.method, r.path) for r in routes}

    assert ("GET", "/health") in route_paths
    assert ("GET", "/api/v1/users/") in route_paths
    assert ("GET", "/api/v1/users/:id") in route_paths
    assert ("POST", "/api/v1/users/") in route_paths
