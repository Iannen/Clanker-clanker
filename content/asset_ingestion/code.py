from asset_ingestion.translation_system.config_dtos import ConfigTranslator
from asset_ingestion.commons.error_collector import ErrorCollector
from app.deps.ingestion import Report
from app.models import Button, RuntimeConfig, Keyboard, ConfigAssembly, CfgFragments
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class DomainOverflow:
    sys_cfg_name: str
    row_keys: str
    domain_names: list[str]
    cfg_filename: str
    overflow_count: int

    def get_msg(self) -> str:
        overflowing = ", ".join(self.domain_names[-self.overflow_count:])
        return (
            f"Domain overflow in '{self.cfg_filename}' ({self.sys_cfg_name}): "
            f"{self.overflow_count} domain(s) overflowed key slots '{self.row_keys}'. "
            f"Excess domains: [{overflowing}]"
        )



