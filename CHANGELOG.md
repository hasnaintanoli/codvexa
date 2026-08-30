# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-08-30

### Changed
- Updated official maintainer contact email to `codvexa.dev@gmail.com`
- Refined author and maintainer metadata fields in distribution packages
- Dynamically synchronized version assertions across the test suite

## [0.1.0] - 2026-08-30

### Added
- Initial Codvexa CLI interface (`codvexa scan`, `codvexa --version`, `codvexa --help`)
- High-performance project file scanner for `.js`, `.jsx`, `.ts`, and `.tsx` source files
- Automatic project metadata and framework detection (Express.js)
- AST-based Express.js route detection powered by Tree-sitter
- Extraction of HTTP methods (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS`, `HEAD`, `ALL`)
- Extraction of route paths, handler names, line numbers, and middleware chains
- Support for chained route declarations (`app.route()`, `router.route()`)
- Multi-file router mounting prefix resolution (`app.use('/api', router)`)
- Formatted CLI terminal table output with ANSI color coding
- Structured JSON export with `--json` and `--output <path>` flags
- Robust error handling for malformed code and unreadable files
- Comprehensive automated test suite with pytest
- Complete documentation and sample API demonstration
