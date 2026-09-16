from abc import ABC, abstractmethod
from dataclasses import dataclass
from app.entities import Keyboard, Resolver, Render
from app.presentation import ActionResult

@dataclass
class RenderContext:
    render: Render
    keyboard: Keyboard
    base_resolvers: list[Resolver]

class KBService(ABC):
    @abstractmethod
    def setup(self, keyboard: Keyboard, base_resolvers: list[Resolver]) -> None: ...
    @abstractmethod
    def handle_key(self, key: str) -> tuple[ActionResult | None, RenderContext | None]: ...