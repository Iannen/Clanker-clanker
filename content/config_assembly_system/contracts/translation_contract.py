from __future__ import annotations
from abc import ABC, abstractmethod
import copy
import re
from typing import Any
from models import *


class FilesetMapABC(ABC):
    @abstractmethod
    def get(self, key: str) -> FileSet | None: ...

    @abstractmethod
    def merge(self, other: FilesetMapABC) -> FilesetMapABC: ...


class ConfigTranslatorABC(ABC):
    @abstractmethod
    def set_collector(self, collector: ErrorCollector) -> None: ...

    @abstractmethod
    def get_collector(self) -> ErrorCollector: ...

    @abstractmethod
    def extract_filesets(
        self, doms_cfg_dict: dict[str, Any]
    ) -> FilesetMapABC: ...

    @abstractmethod
    def set_filesetmap(self, filesetmap: FilesetMapABC) -> None: ...

    @abstractmethod
    def extract_domains(
        self,
        doms_cfg_dict: dict[str, Any],
    ) -> list[Domain]: ...

    @abstractmethod
    def process_sys_cfg(
        self, sys_cfg: dict[str, Any]
    ) -> tuple[Render, KbSpec]: ...

    @abstractmethod
    def get_resolvers(
        self,
        shared_domains_data: dict[str, Any],
    ) -> list[Resolver]: ...