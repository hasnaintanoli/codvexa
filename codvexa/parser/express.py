"""
Express.js route discovery using Tree-sitter AST parsing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import tree_sitter
import tree_sitter_javascript
import tree_sitter_typescript

from codvexa.models.route import Route, ScanError

# Initialize Tree-sitter languages and parsers
_JS_LANGUAGE = tree_sitter.Language(tree_sitter_javascript.language())
_TS_LANGUAGE = tree_sitter.Language(tree_sitter_typescript.language_typescript())
_TSX_LANGUAGE = tree_sitter.Language(tree_sitter_typescript.language_tsx())

HTTP_METHODS = {
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "options",
    "head",
    "all",
}


@dataclass
class RawRoute:
    """An un-prefixed route extracted directly from AST."""

    method: str
    path: str
    file: str
    line: int
    handler: Optional[str] = None
    router: Optional[str] = None
    middlewares: List[str] = field(default_factory=list)


@dataclass
class RouterMount:
    """A mounting point (e.g. app.use('/api', router))."""

    prefix: str
    router_name: Optional[str] = None
    module_spec: Optional[str] = None
    line: int = 0


@dataclass
class ModuleImport:
    """A require() or import statement mapping a variable to a module path."""

    variable_name: str
    module_spec: str
    line: int = 0


@dataclass
class FileParseResult:
    """Information extracted from a single source file."""

    file_path: str
    routes: List[RawRoute] = field(default_factory=list)
    mounts: List[RouterMount] = field(default_factory=list)
    imports: List[ModuleImport] = field(default_factory=list)
    exported_routers: Set[str] = field(default_factory=set)
    errors: List[ScanError] = field(default_factory=list)


def _get_parser_for_path(path_str: str) -> tree_sitter.Parser:
    """Return appropriate Tree-sitter parser based on file extension."""
    suffix = Path(path_str).suffix.lower()
    if suffix in {".ts", ".mts", ".cts"}:
        return tree_sitter.Parser(_TS_LANGUAGE)
    elif suffix == ".tsx":
        return tree_sitter.Parser(_TSX_LANGUAGE)
    elif suffix == ".jsx":
        return tree_sitter.Parser(_TSX_LANGUAGE)
    else:
        return tree_sitter.Parser(_JS_LANGUAGE)


def _node_text(node: tree_sitter.Node) -> str:
    """Extract UTF-8 text from an AST node."""
    return node.text.decode("utf-8", errors="replace")


def _extract_string_value(node: tree_sitter.Node) -> Optional[str]:
    """Extract literal string value without enclosing quotes."""
    if node.type == "string":
        text = _node_text(node)
        if len(text) >= 2 and text[0] in ('"', "'", "`") and text[-1] in ('"', "'", "`"):
            return text[1:-1]
        return text
    elif node.type == "template_string":
        text = _node_text(node)
        if len(text) >= 2 and text[0] == "`" and text[-1] == "`":
            return text[1:-1]
        return text
    elif node.type == "binary_expression":
        # Handle simple string concatenation like "/api" + "/users"
        left = node.child_by_field_name("left")
        right = node.child_by_field_name("right")
        op = node.child_by_field_name("operator")
        if left and right and op and _node_text(op) == "+":
            left_val = _extract_string_value(left)
            right_val = _extract_string_value(right)
            if left_val is not None and right_val is not None:
                return left_val + right_val
    return None


def _extract_handler_name(node: tree_sitter.Node) -> str:
    """Extract a human-readable name for a handler node."""
    if node.type == "identifier":
        return _node_text(node)
    elif node.type == "member_expression":
        return _node_text(node)
    elif node.type in ("arrow_function", "function_expression", "function"):
        # Check if function expression has a declared identifier name
        for child in node.children:
            if child.type == "identifier":
                return _node_text(child)
        return "<anonymous>"
    elif node.type == "call_expression":
        func_node = node.child_by_field_name("function")
        if func_node:
            return _node_text(func_node)
        return _node_text(node)
    return _node_text(node)


def combine_paths(prefix: str, subpath: str) -> str:
    """
    Combine a mounting prefix and a route subpath cleanly.

    Examples:
        combine_paths('/api', '/users') -> '/api/users'
        combine_paths('/api/users', '/') -> '/api/users/'
        combine_paths('/api/users', '/:id') -> '/api/users/:id'
    """
    prefix = prefix.strip()
    subpath = subpath.strip()

    if not prefix or prefix == "/":
        if not subpath:
            return "/"
        return subpath if subpath.startswith("/") else f"/{subpath}"

    if not subpath or subpath == "/":
        if subpath == "/":
            return f"{prefix.rstrip('/')}/"
        return prefix if prefix.startswith("/") else f"/{prefix}"

    p = prefix.rstrip("/")
    s = subpath.lstrip("/")
    res = f"{p}/{s}"
    if not res.startswith("/"):
        res = f"/{res}"
    return res


class ExpressASTExtractor:
    """Extracts raw routes, mounts, imports, and exports from an AST."""

    def __init__(self, source_bytes: bytes, parser: tree_sitter.Parser, file_path: str = ""):
        self.source_bytes = source_bytes
        self.parser = parser
        self.file_path = file_path
        self.routes: List[RawRoute] = []
        self.mounts: List[RouterMount] = []
        self.imports: List[ModuleImport] = []
        self.exported_routers: Set[str] = set()
        self.errors: List[ScanError] = []
        self._handled_chained_calls: Set[int] = set()

    def parse(self) -> FileParseResult:
        try:
            tree = self.parser.parse(self.source_bytes)
        except Exception as exc:
            self.errors.append(ScanError(file=self.file_path, reason=f"AST parse error: {exc}"))
            return FileParseResult(
                file_path=self.file_path,
                routes=[],
                mounts=[],
                imports=[],
                exported_routers=set(),
                errors=self.errors,
            )

        self._visit(tree.root_node)

        return FileParseResult(
            file_path=self.file_path,
            routes=self.routes,
            mounts=self.mounts,
            imports=self.imports,
            exported_routers=self.exported_routers,
            errors=self.errors,
        )

    def _visit(self, node: tree_sitter.Node):
        if node.type == "call_expression":
            self._handle_call_expression(node)
        elif node.type in ("lexical_declaration", "variable_declaration"):
            self._handle_variable_declaration(node)
        elif node.type == "import_statement":
            self._handle_import_statement(node)
        elif node.type in ("export_statement", "expression_statement"):
            self._handle_export_statement(node)

        for child in node.children:
            self._visit(child)

    def _handle_call_expression(self, node: tree_sitter.Node):
        if id(node) in self._handled_chained_calls:
            return

        func = node.child_by_field_name("function")
        args_node = node.child_by_field_name("arguments")
        if not func or not args_node:
            return

        if func.type == "member_expression":
            prop = func.child_by_field_name("property")
            obj = func.child_by_field_name("object")
            if not prop or not obj:
                return

            prop_name = _node_text(prop).lower()

            # Handle router mounting: app.use('/prefix', router)
            if prop_name == "use":
                self._parse_use_call(node, obj, args_node)
                return

            # Check if this is an HTTP method call
            if prop_name in HTTP_METHODS:
                # Check for chained .route() pattern
                chain_info = self._unroll_route_chain(node)
                if chain_info is not None:
                    base_obj, route_path, chain_methods = chain_info
                    for method_name, prop_node, call_args, call_node in chain_methods:
                        self._handled_chained_calls.add(id(call_node))
                        self._add_route_from_args(
                            method=method_name,
                            path=route_path,
                            router_name=base_obj,
                            args_node=call_args,
                            line=prop_node.start_point.row + 1,
                            is_chained=True,
                        )
                else:
                    self._parse_direct_route(node, prop_name, obj, args_node)

    def _unroll_route_chain(
        self, node: tree_sitter.Node
    ) -> Optional[Tuple[str, str, List[Tuple[str, tree_sitter.Node, tree_sitter.Node, tree_sitter.Node]]]]:
        """
        If this call is the outermost call of an app.route('/path').get(...).post(...) chain,
        return (router_name, path, [(method, prop_node, args_node, call_node)]).
        """
        curr = node
        chain: List[Tuple[str, tree_sitter.Node, tree_sitter.Node, tree_sitter.Node]] = []
        base_obj: Optional[str] = None
        route_path: Optional[str] = None

        while curr and curr.type == "call_expression":
            func = curr.child_by_field_name("function")
            if not func or func.type != "member_expression":
                break
            prop = func.child_by_field_name("property")
            obj = func.child_by_field_name("object")
            args = curr.child_by_field_name("arguments")
            if not prop or not obj:
                break
            prop_name = _node_text(prop).lower()

            if prop_name == "route":
                # Found the base route() call
                if args:
                    arg_nodes = [c for c in args.children if c.type not in ("(", ")", ",")]
                    if arg_nodes:
                        route_path = _extract_string_value(arg_nodes[0])
                        if route_path is None:
                            route_path = _node_text(arg_nodes[0]).strip("'\"`")
                base_obj = _node_text(obj)
                break
            elif prop_name in HTTP_METHODS:
                chain.append((prop_name.upper(), prop, args, curr))
                curr = obj
            else:
                break

        if route_path is not None and base_obj is not None and chain:
            chain.reverse()  # Restore source order
            return (base_obj, route_path, chain)

        return None

    def _parse_direct_route(
        self,
        node: tree_sitter.Node,
        method: str,
        obj: tree_sitter.Node,
        args_node: tree_sitter.Node,
    ):
        router_name = _node_text(obj)
        arg_nodes = [c for c in args_node.children if c.type not in ("(", ")", ",")]
        if not arg_nodes:
            return

        # First argument is the route path
        path_arg = arg_nodes[0]
        path_val = _extract_string_value(path_arg)

        if path_val is None:
            # If not a string literal, inspect if identifier or member expression
            if path_arg.type in ("identifier", "member_expression"):
                path_val = _node_text(path_arg)
            else:
                return

        # Ensure path starts with /
        if not path_val.startswith("/") and not path_val.startswith("^"):
            path_val = f"/{path_val}"

        handler_nodes = arg_nodes[1:]
        handlers: List[str] = []
        for h in handler_nodes:
            if h.type == "array":
                for elem in h.children:
                    if elem.type not in ("[", "]", ","):
                        handlers.append(_extract_handler_name(elem))
            else:
                handlers.append(_extract_handler_name(h))

        main_handler = handlers[-1] if handlers else None
        middlewares = handlers[:-1] if len(handlers) > 1 else []
        line = node.start_point.row + 1

        self.routes.append(
            RawRoute(
                method=method.upper(),
                path=path_val,
                file=self.file_path,
                line=line,
                handler=main_handler,
                router=router_name,
                middlewares=middlewares,
            )
        )

    def _add_route_from_args(
        self,
        method: str,
        path: str,
        router_name: str,
        args_node: Optional[tree_sitter.Node],
        line: int,
        is_chained: bool = False,
    ):
        handlers: List[str] = []
        if args_node:
            arg_nodes = [c for c in args_node.children if c.type not in ("(", ")", ",")]
            for h in arg_nodes:
                if h.type == "array":
                    for elem in h.children:
                        if elem.type not in ("[", "]", ","):
                            handlers.append(_extract_handler_name(elem))
                else:
                    handlers.append(_extract_handler_name(h))

        main_handler = handlers[-1] if handlers else None
        middlewares = handlers[:-1] if len(handlers) > 1 else []

        if not path.startswith("/") and not path.startswith("^"):
            path = f"/{path}"

        self.routes.append(
            RawRoute(
                method=method.upper(),
                path=path,
                file=self.file_path,
                line=line,
                handler=main_handler,
                router=router_name,
                middlewares=middlewares,
            )
        )

    def _parse_use_call(
        self,
        node: tree_sitter.Node,
        obj: tree_sitter.Node,
        args_node: tree_sitter.Node,
    ):
        arg_nodes = [c for c in args_node.children if c.type not in ("(", ")", ",")]
        if not arg_nodes:
            return

        prefix: Optional[str] = None
        target_node: Optional[tree_sitter.Node] = None

        if len(arg_nodes) >= 2:
            prefix = _extract_string_value(arg_nodes[0])
            target_node = arg_nodes[1]
        elif len(arg_nodes) == 1:
            prefix = "/"
            target_node = arg_nodes[0]
        else:
            return

        if prefix is None:
            return

        router_target: Optional[str] = None
        module_spec: Optional[str] = None

        if target_node:
            if target_node.type == "identifier":
                router_target = _node_text(target_node)
            elif target_node.type == "call_expression":
                req_func = target_node.child_by_field_name("function")
                if req_func and _node_text(req_func) == "require":
                    req_args = target_node.child_by_field_name("arguments")
                    if req_args:
                        req_arg_nodes = [c for c in req_args.children if c.type not in ("(", ")", ",")]
                        if req_arg_nodes:
                            module_spec = _extract_string_value(req_arg_nodes[0])

        self.mounts.append(
            RouterMount(
                prefix=prefix,
                router_name=router_target,
                module_spec=module_spec,
                line=node.start_point.row + 1,
            )
        )

    def _handle_variable_declaration(self, node: tree_sitter.Node):
        for child in node.children:
            if child.type == "variable_declarator":
                name_node = child.child_by_field_name("name")
                value_node = child.child_by_field_name("value")
                if name_node and value_node and value_node.type == "call_expression":
                    func = value_node.child_by_field_name("function")
                    if func and _node_text(func) == "require":
                        args = value_node.child_by_field_name("arguments")
                        if args:
                            arg_nodes = [c for c in args.children if c.type not in ("(", ")", ",")]
                            if arg_nodes:
                                mod_path = _extract_string_value(arg_nodes[0])
                                if mod_path:
                                    self.imports.append(
                                        ModuleImport(
                                            variable_name=_node_text(name_node),
                                            module_spec=mod_path,
                                            line=node.start_point.row + 1,
                                        )
                                    )

    def _handle_import_statement(self, node: tree_sitter.Node):
        source_node = node.child_by_field_name("source")
        if not source_node:
            return
        mod_path = _extract_string_value(source_node)
        if not mod_path:
            return

        for child in node.children:
            if child.type == "import_clause":
                for clause_child in child.children:
                    if clause_child.type == "identifier":
                        self.imports.append(
                            ModuleImport(
                                variable_name=_node_text(clause_child),
                                module_spec=mod_path,
                                line=node.start_point.row + 1,
                            )
                        )

    def _handle_export_statement(self, node: tree_sitter.Node):
        text = _node_text(node)
        if "module.exports" in text or "export default" in text:
            # Simple heuristic extraction of exported identifier
            for child in node.children:
                if child.type == "identifier":
                    self.exported_routers.add(_node_text(child))


def _resolve_relative_module(
    base_file: str,
    module_spec: str,
    all_file_set: Set[str],
) -> Optional[str]:
    """Resolve a relative import specifier (e.g. './routes/users') to a known project file."""
    if not module_spec.startswith("."):
        return None

    base_dir = Path(base_file).parent
    target = (base_dir / module_spec).as_posix()
    target = Path(target).as_posix()

    candidates = [
        target,
        f"{target}.js",
        f"{target}.ts",
        f"{target}.jsx",
        f"{target}.tsx",
        f"{target}.mjs",
        f"{target}.cjs",
        f"{target}/index.js",
        f"{target}/index.ts",
    ]

    for c in candidates:
        norm_c = Path(c).as_posix()
        if norm_c in all_file_set:
            return norm_c

    return None


def parse_express_routes(source: str, file_path: str = "") -> List[Route]:
    """
    Parse a single JavaScript or TypeScript source code string and extract Express routes.

    Args:
        source: Source code content as string.
        file_path: Relative or display path for the file.

    Returns:
        A list of Route objects.
    """
    source_bytes = source.encode("utf-8")
    parser = _get_parser_for_path(file_path or "index.js")
    extractor = ExpressASTExtractor(source_bytes, parser, file_path=file_path)
    result = extractor.parse()

    # In-file prefix resolution if app.use('/prefix', router) is present in the same file
    router_prefixes: Dict[str, List[str]] = {}
    for mount in result.mounts:
        if mount.router_name:
            router_prefixes.setdefault(mount.router_name, []).append(mount.prefix)

    routes: List[Route] = []
    seen: Set[Tuple[str, str, str, Optional[int]]] = set()

    for raw in result.routes:
        # Check if the router has in-file mount prefixes
        prefixes = router_prefixes.get(raw.router or "", [None])
        for pfx in prefixes:
            final_path = combine_paths(pfx, raw.path) if pfx else raw.path
            key = (raw.method, final_path, raw.file, raw.line)
            if key not in seen:
                seen.add(key)
                routes.append(
                    Route(
                        method=raw.method,
                        path=final_path,
                        file=raw.file,
                        line=raw.line,
                        handler=raw.handler,
                        router=raw.router,
                        middlewares=raw.middlewares,
                    )
                )

    return routes


def parse_project_routes(
    source_files: List[Path],
    project_root: Path,
) -> Tuple[List[Route], List[ScanError]]:
    """
    Parse all source files in a project, resolving multi-file router mounts and prefixes.

    Args:
        source_files: List of absolute or relative Path objects to scan.
        project_root: Project root Path for computing relative paths.

    Returns:
        A tuple of (discovered routes list, scan errors list).
    """
    root_resolved = project_root.resolve()
    rel_files_map: Dict[str, Path] = {}
    all_file_set: Set[str] = set()

    for sf in source_files:
        try:
            rel = sf.resolve().relative_to(root_resolved).as_posix()
        except ValueError:
            rel = sf.name
        rel_files_map[rel] = sf
        all_file_set.add(rel)

    parsed_results: Dict[str, FileParseResult] = {}
    all_errors: List[ScanError] = []

    # Step 1: Parse all files into AST data
    for rel_path, full_path in rel_files_map.items():
        try:
            with open(full_path, "rb") as f:
                source_bytes = f.read()
        except (OSError, PermissionError) as exc:
            all_errors.append(ScanError(file=rel_path, reason=f"Could not read file: {exc}"))
            continue

        parser = _get_parser_for_path(rel_path)
        extractor = ExpressASTExtractor(source_bytes, parser, file_path=rel_path)
        res = extractor.parse()
        parsed_results[rel_path] = res
        all_errors.extend(res.errors)

    # Step 2: Build cross-file and in-file router mount map
    # Maps file_path -> list of prefixes
    file_mount_prefixes: Dict[str, List[str]] = {}
    # Maps (file_path, router_name) -> list of prefixes
    router_mount_prefixes: Dict[Tuple[str, str], List[str]] = {}

    for rel_path, res in parsed_results.items():
        # Build local variable -> module path map
        var_to_module: Dict[str, str] = {}
        for imp in res.imports:
            resolved_mod = _resolve_relative_module(rel_path, imp.module_spec, all_file_set)
            if resolved_mod:
                var_to_module[imp.variable_name] = resolved_mod

        for mount in res.mounts:
            # Case A: app.use('/api', require('./routes/users'))
            if mount.module_spec:
                resolved_mod = _resolve_relative_module(rel_path, mount.module_spec, all_file_set)
                if resolved_mod:
                    file_mount_prefixes.setdefault(resolved_mod, []).append(mount.prefix)

            # Case B: app.use('/api', userRouter) where userRouter is imported
            elif mount.router_name and mount.router_name in var_to_module:
                target_file = var_to_module[mount.router_name]
                file_mount_prefixes.setdefault(target_file, []).append(mount.prefix)

            # Case C: app.use('/api', router) in the same file
            elif mount.router_name:
                router_mount_prefixes.setdefault((rel_path, mount.router_name), []).append(mount.prefix)

    # Step 3: Generate routes with resolved prefixes
    final_routes: List[Route] = []
    seen: Set[Tuple[str, str, str, Optional[int]]] = set()

    for rel_path, res in parsed_results.items():
        # Check if entire file has mounted prefixes
        file_prefixes = file_mount_prefixes.get(rel_path, [])

        for raw in res.routes:
            # Check in-file router prefixes first
            in_file_prefixes = router_mount_prefixes.get((rel_path, raw.router or ""), [])

            candidate_prefixes: List[Optional[str]] = []
            if file_prefixes:
                candidate_prefixes.extend(file_prefixes)
            if in_file_prefixes:
                candidate_prefixes.extend(in_file_prefixes)
            if not candidate_prefixes:
                candidate_prefixes.append(None)

            for pfx in candidate_prefixes:
                final_path = combine_paths(pfx, raw.path) if pfx else raw.path
                key = (raw.method, final_path, raw.file, raw.line)
                if key not in seen:
                    seen.add(key)
                    final_routes.append(
                        Route(
                            method=raw.method,
                            path=final_path,
                            file=raw.file,
                            line=raw.line,
                            handler=raw.handler,
                            router=raw.router,
                            middlewares=raw.middlewares,
                        )
                    )

    # Sort routes by file, line number, and path for clean deterministic ordering
    final_routes.sort(key=lambda r: (r.file, r.line or 0, r.path, r.method))

    return final_routes, all_errors
