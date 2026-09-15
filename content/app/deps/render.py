from abc import ABC, abstractmethod
from app.entities import Render, RuntimeConfig

class RenderService(ABC):
    @abstractmethod
    def hydrate(self, template: str, replacements: dict[str, str]) -> str: ...
    @abstractmethod
    def get_template(self, render: Render) -> str: ...
    @abstractmethod
    def get_repl_map(self, cfg: RuntimeConfig, render: Render) -> dict[str, str]: ...
