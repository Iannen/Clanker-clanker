from typing import Protocol
from models import RuntimeConfig

class RtcAssembler(Protocol):
    def assemble(
        self,
        sys_cfg: dict,
        pud_cfg: dict,
        shared_cfg: dict
    ) -> tuple[Report, RuntimeConfig]: ...

class Report(Protocol):
    def raise_if_any(self) -> None: ...

class ConfigValidatorProtocol(Protocol):
    def assert_no_quotes(self, raw_text: str, filepath: str = "") -> None: ...
    def get_as_dict(self, raw_text: str) -> dict: ...