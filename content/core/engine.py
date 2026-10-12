#!/usr/bin/env -S python3 -B
from stdlib import dataclass
from core import (
    ActionResult,
    ProgramExit,
    HotPromptRequested,
)
from core.engine_deps import IngestionService, KBService, RenderService, TUIService, StartResult, ClankerizeResult, TerminateResult, Declined

@dataclass(slots=True)
class AppEngine:
    io: TUIService
    session: IngestionService
    renderer: RenderService
    kb_service: KBService

    def run(self) -> str:        
        res = self.session.get_runtime_config()
        match res:
            case StartResult(): 
                if res.report.get_complaints():
                    if self.io.confirm_start(res.report) is Declined:
                        return ActionResult.MSG_DECLINED_BOOTSTRAP
                
            case ClankerizeResult():
                if self.io.confirm_clankerize(res.report) is Declined:
                    return ActionResult.MSG_DECLINED_INIT
                res = self.session.initialize_workspace()
            case TerminateResult():
                return self.io.inform_termination(res.report)      

        self.renderer.set_ui_render(res.ui_render)
        self.kb_service.setup(res.kb)
        action_res = ActionResult(ActionResult.BOOTSTRAP_SUCCESS)            

        try:
            while True:
                ui_render_ctx = self.kb_service.get_ui_context()
                ui_render = self.renderer.render_ui(ui_render_ctx, action_res)
                self.io.display(ui_render)
                cmd_key = self.io.get_key()
                try:
                    new_action_res, prompt_render_ctx = self.kb_service.handle_key(cmd_key)
                except HotPromptRequested:
                    hot_ctx = self.kb_service.get_hot_prompt_context()
                    rendered_text = self.renderer.render_prompt(hot_ctx)
                    action_res = self.io.to_clipboard(rendered_text)
                else:
                    if new_action_res is not None:
                        action_res = new_action_res
                    elif prompt_render_ctx is not None:
                        rendered_text = self.renderer.render_prompt(prompt_render_ctx)
                        action_res = self.io.to_clipboard(rendered_text)
        except ProgramExit:
            return ActionResult.MSG_DEFAULT