#!/usr/bin/env -S python3 -B
from stdlib import dataclass
from core import (
    ActionResult,
    UserQuestions,
    UserDecline,
    ProgramExit,
    HotPromptRequested,
)
from core.engine_deps import IngestionService, KBService, RenderService, TUIService, StartResult, ClankerizeResult, TerminateResult

@dataclass(slots=True)
class AppEngine:
    io: TUIService
    session: IngestionService
    renderer: RenderService
    kb_service: KBService

    def run(self) -> str:       
        """
        Have to deal with report.
        I think I send it to io, and receive in return 

        Also I think actionresult becomes a dto baseclass, for when services get back to engine about something. 
        """
        res = self.session.get_runtime_config()
        match res:
            case StartResult(): 
                #send report to io.confirmboot(), get actionresult to match on for run scope storage or str extraction if user declines.
                #it doesnt bother user if report is all clear, only translates into proper actionresult
                pass 
            case ClankerizeResult():
                # pass report to io.confirmclankerize, who asks user if he wants to clankerize if complaints
                # returns an actionresult for each of (yes/nocomplaint) or no
                try:
                    self.io.get_confirmation(
                        UserQuestions.INIT_REPO, UserQuestions.REQUIRED_PHRASE
                    )
                except UserDecline:
                    return ActionResult.MSG_DECLINED_INIT
                res = self.session.initialize_workspace()
            case TerminateResult():
                # so it becomes a 'tell the user this shit' method on io, returning only a single actionresult
                all_crits = res.report.get_critical_complaints()
                all_softs = res.report.get_complaints()
                msg = "Critical errors:\n" + "\n".join(all_crits)
                if all_softs:
                    msg += "\nSoft complaints:\n" + "\n".join(all_softs)
                return msg                

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