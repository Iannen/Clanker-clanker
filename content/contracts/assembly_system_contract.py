from models import RuntimeConfig

from abc import ABC, abstractmethod
from models import RuntimeConfig

class RtcAssembler(ABC):
    @abstractmethod
    def assemble(
        self,
        sys_cfg: dict,
        pud_cfg: dict,
        shared_cfg: dict
    ) -> tuple[Report, RuntimeConfig]: ...

class Report(ABC):
    @abstractmethod
    def raise_if_any(self) -> None: ...