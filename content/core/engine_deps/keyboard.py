from stdlib import ABC, abstractmethod, dataclass
from core import Resolver, Render, ActionResult, Keyboard

@dataclass
class RenderContext:
    kb: Keyboard
    render: Render

@dataclass
class UIRenderContext:
    kb: Keyboard

class KBService(ABC):
    @abstractmethod
    def setup(self, kb: Keyboard) -> None: ...
    @abstractmethod
    def handle_key(self, key: str) -> tuple[ActionResult | None, RenderContext | None]: ...
    @abstractmethod
    def get_ui_context(self) -> UIRenderContext: ...
    @abstractmethod
    def get_hot_prompt_context(self) -> RenderContext: ...