from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import re

import functools

def shadow_of(impl_class):
    def decorator(cls):
        @functools.wraps(impl_class.__init__ if hasattr(impl_class, "__init__") and impl_class.__init__ is not object.__init__ else lambda self, *a, **kw: None)
        def new_init(self, *args, **kwargs):
            self._impl = impl_class(*args, **kwargs)
            real_methods = {m for m in dir(impl_class) if not m.startswith("_")}
            shadow_methods = {m for m in dir(cls) if not m.startswith("_")}
            missing = real_methods - shadow_methods
            if missing:
                raise TypeError(f"{cls.__name__} out of sync. Missing: {missing}")

        cls.__init__ = new_init

        real_methods = [m for m in dir(impl_class) if not m.startswith("_")]
        for method_name in real_methods:
            def make_delegated(name):
                original_method = getattr(impl_class, name)
                
                def class_delegated(cls_target, *args, **kwargs):
                    instance = cls_target()
                    res = getattr(instance._impl, name)(*args, **kwargs)
                    if res is instance._impl:
                        return instance
                    return res

                def instance_delegated(self_target, *args, **kwargs):
                    res = getattr(self_target._impl, name)(*args, **kwargs)
                    if res is self_target._impl:
                        return self_target
                    return res

                class DualMethod:
                    def __get__(self, instance, owner):
                        if instance is None:
                            return lambda *a, **kw: class_delegated(owner, *a, **kw)
                        else:
                            return lambda *a, **kw: instance_delegated(instance, *a, **kw)

                return DualMethod()

            setattr(cls, method_name, make_delegated(method_name))

        return cls
    return decorator

class Expectance(ABC):
    @abstractmethod
    def to_result(self, run_state: dict) -> Result:
        pass

class ExitMsgImpl(Expectance):
    def __init__(self) -> None:
        self.expected_msg = ""

    def contains(self, expected_msg: str) -> "ExitMsgImpl":
        self.expected_msg = expected_msg
        return self

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
    def __init__(self) -> None:
        self.expected_text = ""

    def contains(self, expected_text: str) -> "StderrContainsImpl":
        self.expected_text = expected_text
        return self

    def to_result(self, run_state: dict) -> Result:
        actual = run_state.get("stderr", "")
        passed = self.expected_text in actual
        details = "" if passed else f"Expected stderr to contain '{self.expected_text}', got '{actual}'"
        return Result(assertion=f"Stderr contains '{self.expected_text}'", passed=passed, details=details)

class DiskStateImpl(Expectance):
    def __init__(self) -> None:
        self.expected_paths = []

    def has(self, expected_paths: list[str] | set[str]) -> "DiskStateImpl":
        self.expected_paths = list(expected_paths)
        return self

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
    def __init__(self) -> None:
        self.template = ""
        self.validators: dict[str, callable] = {}

    def contains(self, template: str) -> "UIRenderImpl":
        self.template = template
        return self

    def where(self, field: str, predicate: callable) -> "UIRenderImpl":
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
    def __init__(self) -> None:
        self.expected_prompt = ""
        self.minimum_lines = None

    def contains(self, expected_prompt: str) -> "PromptRenderImpl":
        self.expected_prompt = expected_prompt
        return self

    def min_lines(self, count: int) -> "PromptRenderImpl":
        self.minimum_lines = count
        return self

    def to_result(self, run_state: dict) -> Result:
        rendered_prompts = run_state.get("rendered_prompts", [])
        latest_prompt = rendered_prompts[-1] if rendered_prompts else ""

        passed = True
        failures = []

        if self.expected_prompt and self.expected_prompt not in latest_prompt:
            passed = False
            failures.append(f"Expected prompt text '{self.expected_prompt}' not found.")

        if self.minimum_lines is not None:
            line_count = len(latest_prompt.splitlines()) if latest_prompt else 0
            if line_count < self.minimum_lines:
                passed = False
                failures.append(
                    f"Expected at least {self.minimum_lines} lines, got {line_count}."
                )

        assertion_parts = []
        if self.expected_prompt:
            assertion_parts.append(f"contains '{self.expected_prompt}'")
        if self.minimum_lines is not None:
            assertion_parts.append(f"min_lines >= {self.minimum_lines}")

        assertion = f"Prompt render check ({', '.join(assertion_parts)})"
        details = "\n".join(failures) if not passed else ""
        return Result(assertion=assertion, passed=passed, details=details)

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