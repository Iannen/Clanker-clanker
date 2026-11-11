import unittest
from backend.asset_ingestion.ingestion_parser import IngestionParser


class TestIngestionParser(unittest.TestCase):

    def setUp(self):
        self.parser = IngestionParser()

    def test_create(self):
        raw = (
            "¤ create: src/calculator.py ¤\n"
            "```python\n"
            "def add(a: int, b: int) -> int:\n"
            "    return a + b\n"
            "```\n"
            "¤ create: src/calculator.py ¤\n"
        )
        result = self.parser.parse(raw)
        self.assertEqual(
            result.creates, 
            [("src/calculator.py", "def add(a: int, b: int) -> int:\n    return a + b")]
        )
        self.assertEqual(result.updates, [])
        self.assertEqual(result.deletes, [])
        self.assertEqual(result.errors, [])

    def test_update(self):
        raw = (
            "¤ update: src/calculator.py ¤\n"
            "```python\n"
            "def subtract(a: int, b: int) -> int:\n"
            "    return a - b\n"
            "```\n"
            "¤ update: src/calculator.py ¤\n"
        )
        result = self.parser.parse(raw)
        self.assertEqual(result.creates, [])
        self.assertEqual(
            result.updates, 
            [("src/calculator.py", "def subtract(a: int, b: int) -> int:\n    return a - b")]
        )
        self.assertEqual(result.deletes, [])
        self.assertEqual(result.errors, [])

    def test_delete(self):
        raw = (
            "¤ delete: src/old_calculator.py ¤\n"
            "¤ delete: tests/test_old_calculator.py ¤\n"
        )
        result = self.parser.parse(raw)
        self.assertEqual(result.creates, [])
        self.assertEqual(result.updates, [])
        self.assertEqual(
            result.deletes, 
            ["src/old_calculator.py", "tests/test_old_calculator.py"]
        )
        self.assertEqual(result.errors, [])

    def test_missing_closer(self):
        raw = (
            "¤ create: src/foo.py ¤\n"
            "```python\n"
            "x = 1\n"
            "```\n"
        )
        result = self.parser.parse(raw)
        self.assertEqual(result.creates, [])
        self.assertEqual(result.updates, [])
        self.assertEqual(result.deletes, [])
        self.assertEqual(len(result.errors), 1)
        self.assertIn("create", result.errors[0])
        self.assertIn("src/foo.py", result.errors[0])
