from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import re

class ShadowBase:
    IMPL_CLASS = None

    def __init__(self, *args, **kwargs) -> None:
        self._impl = self.IMPL_CLASS(*args, **kwargs)
        real_methods = {m for m in dir(self.IMPL_CLASS) if not m.startswith("_")}
        shadow_methods = {m for m in dir(self) if not m.startswith("_")}
        missing = real_methods - shadow_methods
        if missing:
            raise TypeError(f"{self.__class__.__name__} out of sync. Missing: {missing}")

class Expectance(ABC):
    @abstractmethod
    def to_result(self, run_state: dict) -> Result:
        pass

class ExitMsgImpl(Expectance):
    def __init__(self, expected_msg: str) -> None:
        self.expected_msg = expected_msg

    def to_result(self, run_state: dict) -> Result:
        actual = run_state.get("exit_msg")
        passed = self.expected_msg in actual

        assertion = f"ExitMsg contains '{self.expected_msg}'"
        
        details = "" if passed else f"Expected exit_msg '{self.expected_msg}', got '{actual}'"
        return Result(
            assertion=assertion,
            passed=passed,
            details=details,
        )

class StderrContainsImpl(Expectance):
    def __init__(self, expected_text: str) -> None:
        self.expected_text = expected_text

    def to_result(self, run_state: dict) -> Result:
        actual = run_state.get("stderr", "")
        passed = self.expected_text in actual
        details = "" if passed else f"Expected stderr to contain '{self.expected_text}', got '{actual}'"
        return Result(assertion=f"Stderr contains '{self.expected_text}'", passed=passed, details=details)

class DiskStateImpl(Expectance):
    def __init__(self, expected_paths: list[str] | set[str]) -> None:
        self.expected_paths = list(expected_paths)

    def to_result(self, run_state: dict) -> Result:
        actual_paths = set(run_state.get("disk_paths"))
        
        missing = []
        for expected in self.expected_paths:
            rel_path = expected
            if rel_path.startswith("<PUD>"):
                rel_path = rel_path[len("<PUD>"):].lstrip("/")
            if rel_path not in actual_paths:
                missing.append(expected)

        passed = len(missing) == 0
        assertion = "Disk state matches expected repository contract paths"
        details = "" if passed else f"Missing expected paths on disk: {missing}"
        return Result(assertion=assertion, passed=passed, details=details)

class UIRenderImpl(Expectance):
    def __init__(self, template: str) -> None:
        self.template = template
        self.validators: dict[str, callable] = {}

    def where(self, field: str, predicate: callable) -> "UIRender":
        self.validators[field] = predicate
        return self

    def to_result(self, run_state: dict) -> Result:
        ui_frames = run_state.get("ui_frames", [])
        latest_frame = ui_frames[-1] if ui_frames else "(No UI frames captured)"

        regex_pattern = re.sub(r"\{(\w+)\}", r"(?P<\1>.+?)", re.escape(self.template))

        parts = []
        last_idx = 0
        field_names = []
        for match in re.finditer(r"\{(\w+)\}", self.template):
            parts.append(re.escape(self.template[last_idx:match.start()]))
            field_name = match.group(1)
            field_names.append(field_name)
            parts.append(f"(?P<{field_name}>.+?)")
            last_idx = match.end()
        parts.append(re.escape(self.template[last_idx:]))
        built_regex = "".join(parts)

        match = re.search(built_regex, latest_frame)
        passed = bool(match)
        details = ""

        if passed and match:
            # Evaluate fluent .where() validators if any exist
            for field, predicate in self.validators.items():
                val = match.group(field)
                if not predicate(val):
                    passed = False
                    details = f"Validation failed for field '{field}' with value '{val}'"
                    break
        elif not passed:
            details = f"Expected UI pattern not found: '{self.template}'\n\n--- Latest UI Render ---\n{latest_frame}"

        assertion = f"Latest UI render matches template: '{self.template}'"
        return Result(assertion=assertion, passed=passed, details=details)

class PromptRenderImpl(Expectance):
    def __init__(self, expected_prompt: str) -> None:
        self.expected_prompt = expected_prompt

@dataclass
class AtomicTest:
    sequence: list[str]
    expects: list[Expectance] | Expectance
    name: str = ""
    reset_sequence: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.expects, list):
            self.expects = [self.expects]

@dataclass
class Result:
    assertion: str = ""
    passed: bool = False
    details: str = ""

    def to_dict(self) -> dict:
        res = {
            "assertion": self.assertion,
            "passed": self.passed,
        }
        if self.details:
            res["details"] = self.details
        return res