# Codvexa

> **Understand the architecture behind your code.**

[![PyPI version](https://img.shields.io/pypi/v/codvexa.svg)](https://pypi.org/project/codvexa/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/hasnaintanoli/codvexa/actions/workflows/ci.yml/badge.svg)](https://github.com/hasnaintanoli/codvexa/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tree-sitter](https://img.shields.io/badge/Parser-Tree--sitter-orange.svg)](https://tree-sitter.github.io/tree-sitter/)

**Codvexa** is an open-source static code analysis and architecture visualization tool for backend applications. It analyzes backend source code to help engineering teams understand their API architecture, routing surfaces, and architectural dependencies.

---

## 🎯 Scope of v0.1

For **v0.1**, Codvexa focuses on doing one core foundation task reliably:

> **Scanning JavaScript and TypeScript backend projects and automatically discovering Express.js API routes using AST static code parsing.**

No LLM, no external network calls, and no runtime code execution required. Codvexa operates 100% locally and safely on your codebase.

---

## ✨ Features

- 🔍 **Recursive Source Scanner**: Traverses project trees for `.js`, `.jsx`, `.ts`, and `.tsx` source files while safely ignoring build artifacts (`node_modules`, `dist`, `.git`, `.next`, etc.).
- 🌳 **Tree-sitter AST Engine**: Accurate syntax tree parsing for JavaScript and TypeScript without brittle regex heuristics.
- ⚡ **Express Route Detection**: Discovers `app.get()`, `router.post()`, `app.put()`, `app.delete()`, `app.patch()`, `app.options()`, `app.head()`, and `app.all()`.
- 🔗 **Chained Route Unrolling**: Extracts routes declared with `app.route('/path').get(...).post(...)`.
- 🛡️ **Router Prefix Resolution**: Resolves single-file and cross-file mounting prefixes (e.g. `app.use('/api/v1/users', usersRouter)`).
- 📌 **Location & Handler Metadata**: Extracts HTTP method, path, relative file path, 1-indexed line number, middleware names, and controller/handler names.
- 📊 **Clean CLI Output**: Formatted terminal output with clean column alignment and ANSI color coding.
- 💾 **JSON Export**: Export full structured route catalogs to JSON format or pipe directly to stdout (`--json` or `--output`).
- 🛡️ **Fault-Tolerant & Local-Only**: Gracefully recovers from syntax errors in malformed files without crashing scans; never sends code over network.

---

## 📦 Installation

Install Codvexa in editable mode or from source:

```bash
git clone https://github.com/hasnaintanoli/codvexa.git
cd codvexa
pip install -e .
```

To install with development and test dependencies:

```bash
pip install -e ".[dev]"
```

---

## 🚀 CLI Usage

### Basic Scan

Scan a project directory:

```bash
codvexa scan ./examples/sample-api
```

Or scan the current directory:

```bash
codvexa scan .
```

### JSON Output to Stdout

Output pure JSON directly (useful for piping into `jq` or CI/CD pipelines):

```bash
codvexa scan ./my-api --json
```

### Export to File

Save the discovered routes and project metadata to a file:

```bash
codvexa scan ./my-api --output routes.json
```

### Diagnostics & Verbose Mode

Enable verbose output:

```bash
codvexa scan ./my-api --verbose
```

### Help and Version

```bash
codvexa --help
codvexa scan --help
codvexa --version
```

---

## 🖥️ Example Terminal Output

```text
Codvexa v0.1.0
────────────────────────────────────────

Project: sample-api
Language: JavaScript
Framework: Express

Scanning project...

✓ Files scanned: 2
✓ API routes found: 8

Routes
────────────────────────────────────────

GET     /health              examples/sample-api/app.js:9
POST    /auth/login          examples/sample-api/app.js:14
GET     /posts               examples/sample-api/app.js:20
POST    /posts               examples/sample-api/app.js:23
GET     /api/users/          examples/sample-api/routes/users.js:30
POST    /api/users/          examples/sample-api/routes/users.js:31
GET     /api/users/:id       examples/sample-api/routes/users.js:32
PUT     /api/users/:id       examples/sample-api/routes/users.js:33
DELETE  /api/users/:id       examples/sample-api/routes/users.js:34

────────────────────────────────────────
Scan completed successfully.
```

---

## 📄 JSON Export Schema

When exported via `--output` or `--json`, Codvexa generates structured JSON:

```json
{
  "codvexa_version": "0.1.0",
  "project": "sample-api",
  "framework": "Express",
  "files_scanned": 2,
  "routes_found": 8,
  "routes": [
    {
      "method": "GET",
      "path": "/health",
      "file": "examples/sample-api/app.js",
      "line": 9,
      "handler": "<anonymous>",
      "router": "app"
    },
    {
      "method": "GET",
      "path": "/api/users/",
      "file": "examples/sample-api/routes/users.js",
      "line": 30,
      "handler": "getUsers",
      "router": "router"
    }
  ]
}
```

---

## 📂 Supported File Types & Extensions

- JavaScript: `.js`, `.mjs`, `.cjs`
- React/JSX: `.jsx`
- TypeScript: `.ts`, `.mts`, `.cts`
- React/TSX: `.tsx`

---

## 🧩 Supported Express Route Patterns

| Pattern | Example |
|---|---|
| Direct app methods | `app.get("/users", getUsers)` |
| Router methods | `router.post("/items", createItem)` |
| Async / Arrow functions | `app.get("/health", async (req, res) => {})` |
| Middleware chains | `app.get("/admin", auth, checkRole, getAdmin)` |
| Chained routes | `app.route("/posts").get(list).post(create)` |
| Single-file mounting | `app.use("/api", router)` |
| Cross-file mounting | `app.use("/api/users", require("./routes/users"))` |
| Member expression handlers | `app.get("/users", userController.getAll)` |

---

## ⚠️ Current Limitations (v0.1)

Static code analysis has inherent boundaries in dynamic environments:
1. **Dynamic runtime methods**: Dynamic dispatch like `app[methodName](path, handler)` is not resolved dynamically.
2. **Runtime variable paths**: Dynamically evaluated path expressions (e.g. `app.get(config.getRoute(), handler)`) cannot be statically computed beyond string literals and simple concatenations.
3. **Complex dynamic router factories**: Custom higher-order factory functions returning routers at runtime are not fully traced in v0.1.

Codvexa prioritizes **accuracy over speculative guessing**.

---

## 🗺️ Roadmap

```text
v0.1
✓ Express route discovery

v0.2
□ Better router prefix resolution
□ More route patterns
□ FastAPI support

v0.3
□ Controller detection
□ Service detection
□ Dependency relationships

v0.4
□ Architecture graph

v0.5
□ Mermaid export

v0.6
□ Interactive architecture viewer

v0.7
□ Database relationship discovery

v0.8
□ External API detection

v0.9
□ Git history analysis

v1.0
□ Multi-framework architecture analysis
```

---

## 🧪 Testing & Development

Run the automated test suite with pytest:

```bash
pytest -v
```

Validate package syntax:

```bash
python -m compileall codvexa
```

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/hasnaintanoli/codvexa/issues).

1. Fork the repository
2. Create your branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add support for nested routers'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
