import unittest

from backend.core import entities as e
from backend.core import engine_deps as d
from backend.asset_ingestion import IngestionServiceImpl


class MockDiskPort(d.DiskPort):
    def __init__(self, existing_paths: set[str] | None = None):
        self._existing: set[str] = existing_paths or set()
        self._writes: list[tuple[str, str]] = []
        self._deletes: list[str] = []

    def get_file_contents(self, tokenized_path: str) -> str:
        if tokenized_path in self._existing:
            return "existing-content"
        raise d.NoSuchFile from FileNotFoundError(f"Mock: {tokenized_path} not found")

    def create_dir(self, tokenized_path: str) -> None:
        pass

    def copy_file(self, from_path: str, to_path: str) -> None:
        pass

    def write_file(self, tokenized_path: str, content: str) -> None:
        self._writes.append((tokenized_path, content))

    def delete_file(self, tokenized_path: str) -> None:
        self._deletes.append(tokenized_path)

    def is_cwd_script_dir(self) -> bool:
        return False

    def get_file_paths(self, basepath_token: str, rel_roots: list[str], missing_ok: bool = False) -> set[str]:
        return set()

    def get_dir_manifest(self, basepath_token: str, rel_roots: list[str] | None = None) -> set[str]:
        return set()


class StubConfigParserPort(d.ConfigParserPort):
    def get_as_dict(self, raw_text: str) -> dict:
        return {}


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


class TestIngestionServiceRejection(unittest.TestCase):

    def setUp(self):
        self.files = MockDiskPort()
        self.service = IngestionServiceImpl(files=self.files, cfg_ingestor=StubConfigParserPort())

    def _assert_all_or_nothing(self, result: d.IngestApplyResult) -> None:
        error_lists = [result.parse_errors, result.missing_paths, result.unexpected_paths]
        has_errors = any(len(l) > 0 for l in error_lists)
        happy_lists = [result.created, result.updated, result.deleted]

        if has_errors:
            for l in happy_lists:
                self.assertEqual(l, [], "Happy-path list should be empty when errors are present")
        else:
            for l in error_lists:
                self.assertEqual(l, [], "Error list should be empty when no errors")

    def test_reject_parse_error(self):
        """Subtask 1: unclosed <create> bookend → parse_errors, no disk ops."""
        raw = "\n".join([
            _create_open("src/foo.py"),
            "```python",
            "x = 1",
            "```",
            # no matching closing tag
        ])
        result = self.service.apply_file_changes(raw)

        self._assert_all_or_nothing(result)
        self.assertEqual(len(result.parse_errors), 1)
        self.assertIn("create", result.parse_errors[0])
        self.assertIn("src/foo.py", result.parse_errors[0])
        self.assertEqual(result.created, [])
        self.assertEqual(result.updated, [])
        self.assertEqual(result.deleted, [])
        self.assertEqual(result.missing_paths, [])
        self.assertEqual(result.unexpected_paths, [])

    def test_reject_create_on_existing_path(self):
        """Subtask 2: create a file that already exists → unexpected_paths, no disk ops."""
        tokenized = "<PUD>/src/calculator.py"
        self.files = MockDiskPort(existing_paths={tokenized})
        self.service = IngestionServiceImpl(files=self.files, cfg_ingestor=StubConfigParserPort())

        raw = "\n".join([
            _create_open("src/calculator.py"),
            "```python",
            "def new_thing(): pass",
            "```",
            _create_close(),
        ])
        result = self.service.apply_file_changes(raw)

        self._assert_all_or_nothing(result)
        self.assertEqual(result.unexpected_paths, ["src/calculator.py"])
        self.assertEqual(result.created, [])
        self.assertEqual(result.updated, [])
        self.assertEqual(result.deleted, [])
        self.assertEqual(result.parse_errors, [])
        self.assertEqual(result.missing_paths, [])

    def test_reject_update_on_missing_path(self):
        """Subtask 3: update a file that does not exist → missing_paths, no disk ops."""
        raw = "\n".join([
            _update_open("src/ghost.py"),
            "```python",
            "def ghost(): pass",
            "```",
            _update_close(),
        ])
        result = self.service.apply_file_changes(raw)

        self._assert_all_or_nothing(result)
        self.assertEqual(result.missing_paths, ["src/ghost.py"])
        self.assertEqual(result.created, [])
        self.assertEqual(result.updated, [])
        self.assertEqual(result.deleted, [])
        self.assertEqual(result.parse_errors, [])
        self.assertEqual(result.unexpected_paths, [])

    def test_reject_delete_on_missing_path(self):
        """Subtask 4: delete a file that does not exist → missing_paths, no disk ops."""
        raw = _delete_tag("src/phantom.py")
        result = self.service.apply_file_changes(raw)

        self._assert_all_or_nothing(result)
        self.assertEqual(result.missing_paths, ["src/phantom.py"])
        self.assertEqual(result.created, [])
        self.assertEqual(result.updated, [])
        self.assertEqual(result.deleted, [])
        self.assertEqual(result.parse_errors, [])
        self.assertEqual(result.unexpected_paths, [])