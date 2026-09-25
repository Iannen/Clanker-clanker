#!/usr/bin/env -S python3 -B
import ast
import builtins
from dataclasses import dataclass, field
from pathlib import Path
from reporter import ImportReports, FileReport

module_list = [
    "stdlib",
    "core",
    "core.engine",
    "core.engine_deps",
    "modules",
    "asset_ingestion",
    "keyboard",
    "render_pipeline",
    "tui",
    "adapters",
]


@dataclass
class PolicyRule:
    dir: str
    allowed_imps: list[str] = field(default_factory=list)
    outside_module_list: bool = False


policy = [
    PolicyRule(
        dir="core/core",
        allowed_imps=["stdlib"],
    ),
    PolicyRule(
        dir="core/engine_deps",
        allowed_imps=["stdlib", "core"],
    ),
    PolicyRule(
        dir="core/engine.py",
        allowed_imps=["stdlib", "core", "core.engine_deps"],
    ),
    PolicyRule(
        dir="modules/asset_ingestion",
        allowed_imps=["stdlib", "core", "core.engine_deps", "asset_ingestion"],
    ),
    PolicyRule(
        dir="modules/keyboard",
        allowed_imps=["stdlib", "core", "core.engine_deps", "keyboard"],
    ),
    PolicyRule(
        dir="modules/render_pipeline",
        allowed_imps=["stdlib", "core", "core.engine_deps", "render_pipeline"],
    ),
    PolicyRule(
        dir="modules/tui",
        allowed_imps=["stdlib", "core", "core.engine_deps", "tui"],
    ),
    PolicyRule(
        dir="adapters",
        allowed_imps=["core", "core.engine_deps"],
        outside_module_list=True,
    ),
    PolicyRule(
        dir="test",
        allowed_imps=["all"],
        outside_module_list=True,
    ),
    PolicyRule(
        dir="clanker.py",
        allowed_imps=["core.engine", "adapters", "modules"],
        outside_module_list=True,
    ),
    PolicyRule(
        dir="stdlib.py",
        outside_module_list=True,
    ),
]

class ImportPolicySuite:
    def __init__(self, content_dir: Path) -> None:
        self._content_dir = content_dir

    def run_tests(self) -> ImportReports:
        aggregated_reports = ImportReports()
        for rule in policy:
            paths = self._resolve_rule_paths(rule)
            for file_path in paths:
                report = self._analyze_file(file_path, rule)
                aggregated_reports.reports.append(report)
        return aggregated_reports

    def _resolve_rule_paths(self, rule: PolicyRule) -> list[Path]:
        target = self._content_dir / rule.dir
        if target.is_file():
            return (
                [target]
                if target.name not in ("__init__.py", "stdlib.py")
                else []
            )
        if target.is_dir():
            return [
                p
                for p in target.rglob("*.py")
                if p.name not in ("__init__.py", "stdlib.py")
            ]
        return []

    def _analyze_file(self, file_path: Path, rule: PolicyRule) -> FileReport:
        relative_path = file_path.relative_to(self._content_dir).as_posix()
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)

        imports: dict[str, str] = {}
        forbidden_imports: list[str] = []
        referenced_symbols: set[str] = set()
        local_declarations: set[str] = set()

        allowed_imps = rule.allowed_imps
        allow_outside = rule.outside_module_list

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    full_module = alias.name
                    root_module = full_module.split(".")[0]
                    bound_name = alias.asname or root_module
                    imports[bound_name] = f"import {alias.name}"

                    if not self._is_import_permitted(
                        full_module, allowed_imps, allow_outside
                    ):
                        forbidden_imports.append(
                            f"Line {getattr(node, 'lineno', '?')}: import '{alias.name}' is forbidden for '{relative_path}'"
                        )

            elif isinstance(node, ast.ImportFrom):
                full_module = node.module or ""

                if full_module and not self._is_import_permitted(
                    full_module, allowed_imps, allow_outside
                ):
                    forbidden_imports.append(
                        f"Line {getattr(node, 'lineno', '?')}: from '{full_module}' is forbidden for '{relative_path}'"
                    )

                for alias in node.names:
                    bound_name = alias.asname or alias.name
                    full_src = (
                        f"from {full_module} import {alias.name}"
                        if full_module
                        else f"import {alias.name}"
                    )
                    imports[bound_name] = full_src

            elif isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ):
                local_declarations.add(node.name)
            elif isinstance(node, ast.arg):
                local_declarations.add(node.arg)
            elif isinstance(node, ast.ExceptHandler) and node.name:
                local_declarations.add(node.name)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                local_declarations.add(node.id)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                referenced_symbols.add(node.id)

        dangling_imports = [
            f"Unused import '{bound}' ({src})"
            for bound, src in imports.items()
            if bound not in referenced_symbols
        ]

        builtin_names = set(dir(builtins)) | {
            "__name__",
            "__file__",
            "__doc__",
            "__package__",
            "__spec__",
            "__annotations__",
        }
        undeclared_imports = [
            f"Unresolved symbol '{symbol}'"
            for symbol in referenced_symbols
            if (
                symbol not in imports
                and symbol not in local_declarations
                and symbol not in builtin_names
            )
        ]

        return FileReport(
            rel_path=relative_path,
            forbidden_import_statements=forbidden_imports,
            dangling_imports=dangling_imports,
            undeclared_imports=undeclared_imports,
        )

    def _is_import_permitted(
        self, full_module: str, allowed_imps: list[str], allow_outside: bool
    ) -> bool:
        if "all" in allowed_imps:
            return True

        root_module = full_module.split(".")[0]

        if full_module in allowed_imps or root_module in allowed_imps:
            return True

        if allow_outside and root_module not in module_list:
            return True

        return False