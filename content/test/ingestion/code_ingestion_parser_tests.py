import unittest

from backend.core import entities as e
from backend.asset_ingestion.ingestion_parser import IngestionParser


def _create_open(path: str) -> str:
    return f"{e.Delims.CREATE_FILESET_UL[1]}{path}{e.Delims.FILESET_OPEN_END_TAG[1]}"


def _create_close() -> str:
    return f"{e.Delims.CREATE_FILESET_BL[1]}{e.Delims.FILESET_OPEN_END_TAG_BR[1]}"


def _update_open(path: str) -> str:
    return f"{e.Delims.UPDATE_FILESET_UL[1]}{path}{e.Delims.FILESET_OPEN_END_TAG[1]}"


def _update_close() -> str:
    return f"{e.Delims.UPDATE_FILESET_BL[1]}{e.Delims.FILESET_OPEN_END_TAG_BR[1]}"


def _delete_tag(path: str) -> str:
    return f"{e.Delims.DELETE_FILESET_UL[1]}{path}{e.Delims.FILESET_CLOSED_END_TAG[1]}"


class TestIngestionParser(unittest.TestCase):

    def setUp(self):
        self.parser = IngestionParser()

    def test_create(self):
        raw = "\n".join([
            _create_open("src/calculator.py"),
            "```python",
            "def add(a: int, b: int) -> int:",
            "    return a + b",
            "```",
            _create_close(),
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
            _update_open("src/calculator.py"),
            "```python",
            "def subtract(a: int, b: int) -> int:",
            "    return a - b",
            "```",
            _update_close(),
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
            _delete_tag("src/old_calculator.py"),
            _delete_tag("tests/test_old_calculator.py"),
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
            _create_open("src/foo.py"),
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

    def test_mismatched_closer_not_accepted(self):
        raw = "\n".join([
            _create_open("src/foo.py"),
            "```python",
            "x = 1",
            "```",
            _update_close(),
        ])
        result = self.parser.parse(raw)
        self.assertEqual(result.creates, [])
        self.assertEqual(result.updates, [])
        self.assertEqual(result.deletes, [])
        self.assertEqual(len(result.errors), 1)
        self.assertIn("create", result.errors[0])
        self.assertIn("src/foo.py", result.errors[0])