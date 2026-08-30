"""
Codvexa CLI interface.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

# Ensure UTF-8 output on Windows consoles if supported
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import typer

from codvexa import __version__
from codvexa.exporters.json_export import export_to_json_file, export_to_json_string
from codvexa.models.route import ScanResult
from codvexa.parser.express import parse_project_routes
from codvexa.scanner.files import discover_files
from codvexa.scanner.project import detect_project
from codvexa.utils.output import (
    err_console,
    print_banner,
    print_completion,
    print_errors,
    print_project_summary,
    print_routes_table,
)

app = typer.Typer(
    name="codvexa",
    help="Codvexa — Understand the architecture behind your code.",
    no_args_is_help=True,
    add_completion=False,
)


def version_callback(value: bool):
    """Callback for --version flag."""
    if value:
        typer.echo(f"Codvexa v{__version__}")
        raise typer.Exit(code=0)


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
):
    """Codvexa: Developer tool for backend architecture and API route discovery."""
    pass


@app.command(name="scan")
def scan(
    project_path: Path = typer.Argument(
        ...,
        help="Path to the JavaScript/TypeScript project directory.",
        metavar="PROJECT_PATH",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output discovered routes as raw JSON to stdout.",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Save scan results to a JSON file.",
        metavar="PATH",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output with additional diagnostic information.",
    ),
):
    """
    Scan a project directory to automatically discover Express.js API routes.
    """
    if not project_path.exists():
        err_console.print(f"[bold red]Error:[/bold red] Project path does not exist: {project_path}")
        raise typer.Exit(code=1)

    resolved_path = project_path.resolve()

    # 1. Discover files
    try:
        discovered = discover_files(resolved_path)
    except Exception as exc:
        err_console.print(f"[bold red]Error during file discovery:[/bold red] {exc}")
        raise typer.Exit(code=1)

    # 2. Detect project info
    project_info = detect_project(resolved_path, discovered.source_files)

    # 3. Parse routes
    try:
        routes, errors = parse_project_routes(discovered.source_files, resolved_path)
    except Exception as exc:
        err_console.print(f"[bold red]Error during route parsing:[/bold red] {exc}")
        raise typer.Exit(code=1)

    # Add any file reading failures to errors
    for failed_file, reason in discovered.failed_files:
        from codvexa.models.route import ScanError
        try:
            rel_err = failed_file.relative_to(resolved_path).as_posix()
        except ValueError:
            rel_err = failed_file.name
        errors.append(ScanError(file=rel_err, reason=reason))

    # 4. Construct ScanResult
    scan_result = ScanResult(
        project=project_info,
        files_scanned=len(discovered.source_files),
        total_files=discovered.total_files,
        skipped_files=discovered.skipped_files,
        routes=routes,
        errors=errors,
    )

    # 5. Export to file if requested
    if output:
        try:
            export_to_json_file(scan_result, output)
            if not json_output and verbose:
                typer.echo(f"Exported routes to {output}")
        except Exception as exc:
            err_console.print(f"[bold red]Error writing output file:[/bold red] {exc}")
            raise typer.Exit(code=1)

    # 6. JSON output to stdout
    if json_output:
        json_str = export_to_json_string(scan_result)
        typer.echo(json_str)
        raise typer.Exit(code=0)

    # 7. Standard terminal output
    print_banner()
    print_project_summary(scan_result)

    if errors:
        print_errors(errors, verbose=verbose)

    print_routes_table(scan_result.routes)
    print_completion(scan_result)


if __name__ == "__main__":
    app()
