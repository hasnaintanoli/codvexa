import sys
from typing import List

from rich.console import Console

from codvexa import __version__
from codvexa.models.route import Route, ScanError, ScanResult

# Ensure UTF-8 output on Windows consoles if supported
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

console = Console(safe_box=True)
err_console = Console(stderr=True, safe_box=True)

# Safe divider that renders cleanly on all platforms
DIVIDER = "─" * 40


def format_route_location(route: Route) -> str:
    """Format file and line number as a location string."""
    if route.line is not None:
        return f"{route.file}:{route.line}"
    return route.file


def get_method_color(method: str) -> str:
    """Return styling color for an HTTP method."""
    method_upper = method.upper()
    colors = {
        "GET": "green",
        "POST": "blue",
        "PUT": "yellow",
        "PATCH": "magenta",
        "DELETE": "red",
        "OPTIONS": "cyan",
        "HEAD": "dim",
        "ALL": "bright_white",
    }
    return colors.get(method_upper, "white")


def print_banner() -> None:
    """Print standard Codvexa CLI header."""
    console.print(f"[bold cyan]Codvexa[/bold cyan] [cyan]v{__version__}[/cyan]")
    console.print(f"[dim]{DIVIDER}[/dim]\n")


def print_project_summary(result: ScanResult) -> None:
    """Print project metadata and scan summary."""
    console.print(f"Project: [bold]{result.project.name}[/bold]")
    console.print(f"Language: {result.project.language}")
    console.print(f"Framework: {result.project.framework}\n")
    console.print("Scanning project...\n")
    console.print(f"[green]✓[/green] Files scanned: {result.files_scanned}")
    console.print(f"[green]✓[/green] API routes found: {result.routes_found}\n")


def print_errors(errors: List[ScanError], verbose: bool = False) -> None:
    """Print non-fatal scan or parser errors."""
    if not errors:
        return

    for err in errors:
        err_console.print(f"[yellow]⚠[/yellow] Could not parse: {err.file}")
        err_console.print(f"   Reason: {err.reason}")

    err_console.print("\n[dim]Continuing scan...[/dim]\n")


def print_routes_table(routes: List[Route]) -> None:
    """Print discovered routes in a clean, readable column format."""
    console.print("[bold]Routes[/bold]")
    console.print(f"[dim]{DIVIDER}[/dim]\n")

    if not routes:
        console.print("[yellow]No API routes discovered in project.[/yellow]\n")
        return

    # Calculate optimal column width for path
    max_path_len = max(len(r.path) for r in routes)
    path_col_width = max(max_path_len + 4, 20)

    for route in routes:
        color = get_method_color(route.method)
        method_str = f"[{color}]{route.method:<7}[/{color}]"
        path_str = f"{route.path:<{path_col_width}}"
        loc_str = format_route_location(route)
        console.print(f"{method_str} {path_str} [dim]{loc_str}[/dim]")

    console.print()


def print_completion(result: ScanResult) -> None:
    """Print scan completion footer."""
    console.print(f"[dim]{DIVIDER}[/dim]")
    if result.errors:
        console.print(f"[yellow]Files with errors: {len(result.errors)}[/yellow]")
    console.print("[bold green]Scan completed successfully.[/bold green]\n")
