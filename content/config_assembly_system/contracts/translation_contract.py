from __future__ import annotations
import copy
import re
from typing import Any
from models import *



class FilesetMapProtocol(Protocol):
    def get(self, key: str) -> FileSet | None: ...
    def merge(self, other: FilesetMapProtocol) -> FilesetMapProtocol: ...

class ConfigTranslatorProtocol(Protocol):
    def set_collector(self, collector: ErrorCollector) -> None: ...
    def get_collector(self) -> ErrorCollector: ...
    def extract_filesets(
        self, doms_cfg_dict: dict[str, Any]
    ) -> FilesetMapProtocol: ...
    def set_filesetmap(self, filesetmap: FilesetMapProtocol) -> None: ...
    def extract_domains(
        self,
        doms_cfg_dict: dict[str, Any],
    ) -> list[Domain]: ...
    def process_sys_cfg(
        self, sys_cfg: dict[str, Any]
    ) -> tuple[Render, KbSpec]: ...
    def get_resolvers(
        self,
        shared_domains_data: dict[str, Any],
    ) -> list[Resolver]: ...
