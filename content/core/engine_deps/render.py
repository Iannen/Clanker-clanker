from stdlib import ABC, abstractmethod
from core import Render
from core.engine_deps import RenderContext, UIRenderContext, ActionFeedbackResult

class RenderService(ABC):
    @abstractmethod
    def set_ui_render(self, ui_render: Render) -> None: ...
    @abstractmethod
    def render_ui(self, ctx: UIRenderContext, msg: ActionFeedbackResult) -> str: ...
    @abstractmethod
    def render_prompt(self, ctx: RenderContext) -> str: ...