import re
import shutil
from pathlib import Path
from results import MethodResult, AssertSuiteResult

class AssertSuite:
    TEMPLATE_FIXTURE_NAME = ""

    def __init__(self, sandbox_dir: Path, fixture_dir: Path, clanker_path: Path, factory: ActionsFactoryImpl):
        self.sandbox_dir = sandbox_dir
        self.fixture_dir = fixture_dir
        self.clanker_path = clanker_path
        self.factory = factory

    def run(self) -> "AssertSuiteResult":
        snake_name = re.sub(r"(?<!^)(?=[A-Z])", "_", self.__class__.__name__).lower()
        sandbox_path = self.sandbox_dir / f"active_sandbox_{snake_name}"
        fixture_path = self.fixture_dir / self.TEMPLATE_FIXTURE_NAME

        if fixture_path.exists():
            shutil.copytree(fixture_path, sandbox_path)

        return self._run_methods(sandbox_path)

    def _run_methods(self, sandbox_path: Path) -> "AssertSuiteResult":
        method_results = []

        assert_methods = [
            (name, getattr(self, name))
            for name in self.__class__.__dict__
            if not name.startswith("_") 
            and name not in ("run", "run_class") 
            and callable(getattr(self, name))
        ]

        for method_name, method in assert_methods:
            containers = method(self.factory)
            if not isinstance(containers, list):
                containers = [containers]

            container_results = []
            for idx, container in enumerate(containers, start=1):
                framedump_path = sandbox_path / "framedumps" / f"{method_name}_{idx}.framedump"
                result = container.run(
                    sandbox_path, 
                    self.clanker_path, 
                    framedump_path, 
                    test_number=idx
                )
                container_results.append(result)

            method_results.append(MethodResult(method_name, container_results))

        return AssertSuiteResult(self.__class__.__name__, "", method_results)