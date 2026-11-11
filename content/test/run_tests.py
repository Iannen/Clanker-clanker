#!/usr/bin/env -S python3 -B

import importlib.util
import sys
from pathlib import Path

# Ensure the project root (content/) is on sys.path so `backend` is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

TEST_MODULES: list[str] = [
    "ingestion/code_ingestion_parser_tests.py",
]


def _load_module(rel_path: str) -> object:
    base = Path(__file__).parent
    full_path = base / rel_path
    module_name = full_path.stem

    spec = importlib.util.spec_from_file_location(module_name, full_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    base = Path(__file__).parent
    failures = 0

    for rel_path in TEST_MODULES:
        label = rel_path
        try:
            module = _load_module(rel_path)
            module.run()
            print(f"PASS  {label}")
        except AssertionError as exc:
            failures += 1
            print(f"FAIL  {label}")
            print(f"      {exc}")
        except Exception as exc:
            failures += 1
            print(f"FAIL  {label}")
            print(f"      {type(exc).__name__}: {exc}")

    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()