import unittest
from pathlib import Path


class TestCodebaseTestParity(unittest.TestCase):
    @unittest.skip("Parked while legacy test suite is built out")
    def test_every_source_file_has_a_test_file(self):
        content_root = Path(__file__).resolve().parent.parent
        backend_dir = content_root / "backend"
        web_ui_dir = content_root / "web-ui"
        entrypoint = content_root / "clank-server.py"
        test_dir = content_root / "test"

        source_files = []

        if entrypoint.is_file():
            source_files.append(entrypoint)

        if backend_dir.is_dir():
            for p in backend_dir.rglob("*.py"):
                if p.name != "__init__.py":
                    source_files.append(p)

        if web_ui_dir.is_dir():
            for p in web_ui_dir.rglob("*"):
                if p.is_file() and p.suffix in (".js", ".html"):
                    source_files.append(p)

        test_files = list(test_dir.rglob("*.py"))
        
        missing_tests = []
        for sf in source_files:
            module_stem = sf.stem
            has_matching_test = any(module_stem in tf.name for tf in test_files)
            
            if not has_matching_test:
                rel_path = sf.relative_to(content_root)
                missing_tests.append(str(rel_path))

        self.assertEqual(
            missing_tests,
            [],
            f"Structural parity violation! The following source files have no corresponding test file:\n" +
            "\n".join(f"  - {m}" for m in missing_tests)
        )