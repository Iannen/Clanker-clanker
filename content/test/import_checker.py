#!/usr/bin/env -S python3 -B
import ast
import builtins
import json
from pathlib import Path
   
"""
stdlib module: aggregates stdlib imports used in core
core, dead things: entities, pathconstants, presentation msgs, exception taxonomy, dto
core.engine_deps, interfaces relied upon by engine, fulfiled by modules. interfaces relied upon by modules, fulfilled by adapters
app.engine, the root orchestrator
any module: only from stdlib, app and app.deps (so not engine)
any adapter: only from app, app.deps or anything not from above
"""
module_list = ["stdlib", "core", "engine_deps", "modules", "asset_ingestion", "keyboard", "render_pipeline", "tui", "adapters"]

policy = [
    {
        "dir": "app/core",
        "allowed_imps": ["stdlib"]
    },
    {
        "dir": "app/engine_deps",
        "allowed_imps": ["stdlib", "core"]
    },
    {
        "dir": "app/engine.py",
        "allowed_imps": ["stdlib", "core", "engine_deps"]
    },
    {
        "dir": "modules/asset_ingestion",
        "allowed_imps": ["stdlib", "core", "engine_deps", "asset_ingestion"]
    },
    {
        "dir": "modules/keyboard",
        "allowed_imps": ["stdlib", "core", "engine_deps", "keyboard"]
    },
    {
        "dir": "modules/render_pipeline",
        "allowed_imps": ["stdlib", "core", "engine_deps", "render_pipeline"]
    },
    {
        "dir": "modules/tui",
        "allowed_imps": ["stdlib", "core", "engine_deps", "tui"]
    },
    {
        "dir": "adapters",
        "allowed_imps": ["core", "engine_deps"],
        "outside_module_list": "allowed"
    },
    {
        "dir": "test",
        "allowed_imps": ["all"],
        "outside_module_list": "allowed"
    },
    {
        "dir": "clanker.py",
        "allowed_imps": ["core.engine", "adapters", "modules"],
        "outside_module_list": "allowed"
    },
    {
        "dir": "stdlib.py",
        "outside_module_list": "allowed"
    },
]


class ImportVerifier:
    MODULE_WHITELIST = {"app", "app/deps", "asset_ingestion", "keyboard", "ports_adapters", "render_pipeline", "tui", "stdlib"}
    REL_ROOTS = {"app", "asset_ingestion", "keyboard", "ports_adapters", "render_pipeline", "tui", "stdlib", "content/clanker.py"}

    def __init__(self, content_dir: Path) -> None:
        self._content_dir = content_dir
        self.report: list[dict] = []
        
        path_content_tuples = self._process_roots()
        self._analyze_files(path_content_tuples)

    def _process_roots(self) -> list[tuple[Path, str]]:
        path_content_tuples: list[tuple[Path, str]] = []
        for rel_path_str in self.REL_ROOTS:
            target_path = self._content_dir / rel_path_str

            if target_path.is_file() and target_path.suffix == ".py":
                content = target_path.read_text(encoding="utf-8")
                path_content_tuples.append((target_path, content))

            elif target_path.is_dir():
                for py_file in target_path.rglob("*.py"):
                    content = py_file.read_text(encoding="utf-8")
                    path_content_tuples.append((py_file, content))

        return path_content_tuples

    def _analyze_files(self, path_content_tuples: list[tuple[Path, str]]) -> None:
        for file_path, content in path_content_tuples:
            self.report.append(self._analyze_file(file_path, content))

    def _analyze_file(self, file_path: Path, content: str) -> dict:
        relative_path = f"{self._content_dir.name}/{file_path.relative_to(self._content_dir)}"

        tree = ast.parse(content)

        imports: dict[str, str] = {}  # bound_name -> module/symbol source
        non_whitelisted_imports: list[str] = []
        referenced_symbols: set[str] = set()
        local_declarations: set[str] = set()

        for node in ast.walk(tree):
            # 1. Collect Imports & Whitelist Check
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_module = alias.name.split(".")[0]
                    bound_name = alias.asname or alias.name.split(".")[0]
                    imports[bound_name] = alias.name

                    if root_module not in self.MODULE_WHITELIST:
                        non_whitelisted_imports.append(
                            f"Line {getattr(node, 'lineno', '?')}: import '{alias.name}' not in MODULE_WHITELIST"
                        )

            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                root_module = module_name.split(".")[0] if module_name else ""

                if root_module and root_module not in self.MODULE_WHITELIST:
                    non_whitelisted_imports.append(
                        f"Line {getattr(node, 'lineno', '?')}: from '{module_name}' not in MODULE_WHITELIST"
                    )

                for alias in node.names:
                    bound_name = alias.asname or alias.name
                    imports[bound_name] = f"{module_name}.{alias.name}" if module_name else alias.name

            # 2. Local Scope Declarations
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                local_declarations.add(node.name)
            elif isinstance(node, ast.arg):
                local_declarations.add(node.arg)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                local_declarations.add(node.id)

            # 3. Referenced Symbols
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                referenced_symbols.add(node.id)

        # Rule 2: Dangling Imports
        dangling_imports = [
            f"Unused import '{bound}' ({src})"
            for bound, src in imports.items()
            if bound not in referenced_symbols
        ]

        # Rule 3: Missing Imports
        builtin_names = set(dir(builtins))
        missing_imports = [
            f"Unresolved symbol '{symbol}'"
            for symbol in referenced_symbols
            if (
                symbol not in imports
                and symbol not in local_declarations
                and symbol not in builtin_names
            )
        ]

        return {
            "file": relative_path,
            "violations": {
                "non_whitelisted_imports": non_whitelisted_imports,
                "dangling_imports": dangling_imports,
                "missing_imports": missing_imports,
            },
        }
