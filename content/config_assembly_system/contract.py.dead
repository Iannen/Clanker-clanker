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
