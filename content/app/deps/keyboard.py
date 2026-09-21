from abc import ABC, abstractmethod
from dataclasses import dataclass
from app import Button, Resolver, Render, ActionResult

@dataclass
class RenderContext:
    btn_map: dict[str, Button]
    selected_key: str | None
    render: Render
    base_resolvers: list[Resolver]

@dataclass
class UIRenderContext:
    btn_map: dict[str, Button]
    selected_key: str | None

class KBService(ABC):
    @abstractmethod
    def setup(self, btn_map: dict[str, Button], base_resolvers: list[Resolver]) -> None: ...
    @abstractmethod
    def handle_key(self, key: str) -> tuple[ActionResult | None, RenderContext | None]: ...
    @abstractmethod
    def get_ui_context(self) -> UIRenderContext: ...
    @abstractmethod
    def get_hot_prompt_context(self) -> RenderContext: ...