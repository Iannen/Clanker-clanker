import unittest

from backend.core import entities as e
from backend.asset_ingestion.ingestion_parser import IngestionParser


def _start_bookend(action: str, path: str) -> str:
    return f"{e.Delims.FILESET_START_OPEN} {action}: {path} {e.Delims.FILESET_START_CLOSE}"


def _end_bookend(action: str, path: str) -> str:
    return f"{e.Delims.FILESET_END_OPEN} {action}: {path} {e.Delims.FILESET_END_CLOSE}"


class TestIngestionParser(unittest.TestCase):

    def setUp(self):
        self.parser = IngestionParser()

    def test_create(self):
        raw = "\n".join([
            _start_bookend("create", "src/calculator.py"),
            "```python",
            "def add(a: int, b: int) -> int:",
            "    return a + b",
            "```",
            _end_bookend("create", "src/calculator.py"),
        ])
        result = self.parser.parse(raw)
        self.assertEqual(
            result.creates,
            [("src/calculator.py", "def add(a: int, b: int) -> int:\n    return a + b")]
        )
        self.assertEqual(result.updates, [])
        self.assertEqual(result.deletes, [])
        self.assertEqual(result.errors, [])

    def test_update(self):
        raw = "\n".join([
            _start_bookend("update", "src/calculator.py"),
            "```python",
            "def subtract(a: int, b: int) -> int:",
            "    return a - b",
            "```",
            _end_bookend("update", "src/calculator.py"),
        ])
        result = self.parser.parse(raw)
        self.assertEqual(result.creates, [])
        self.assertEqual(
            result.updates,
            [("src/calculator.py", "def subtract(a: int, b: int) -> int:\n    return a - b")]
        )
        self.assertEqual(result.deletes, [])
        self.assertEqual(result.errors, [])

    def test_delete(self):
        raw = "\n".join([
            _start_bookend("delete", "src/old_calculator.py"),
            _start_bookend("delete", "tests/test_old_calculator.py"),
        ])
        result = self.parser.parse(raw)
        self.assertEqual(result.creates, [])
        self.assertEqual(result.updates, [])
        self.assertEqual(
            result.deletes,
            ["src/old_calculator.py", "tests/test_old_calculator.py"]
        )
        self.assertEqual(result.errors, [])

    def test_missing_closer(self):
        raw = "\n".join([
            _start_bookend("create", "src/foo.py"),
            "```python",
            "x = 1",
            "```",
        ])
        result = self.parser.parse(raw)
        self.assertEqual(result.creates, [])
        self.assertEqual(result.updates, [])
        self.assertEqual(result.deletes, [])
        self.assertEqual(len(result.errors), 1)
        self.assertIn("create", result.errors[0])
        self.assertIn("src/foo.py", result.errors[0])