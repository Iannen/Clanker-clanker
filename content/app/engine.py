#!/usr/bin/env -S python3 -B
import traceback
from typing import Any
from app.presentation import ActionResult, UserQuestions
from app.exceptions import ExceptionPolicy, UserDecline, NoConfig, ProgramExit, HotPromptRequested
from app.deps import *
from app.deps.keyboard import KBService

class AppEngine:
    def __init__(
        self, 
        io: TUIService, 
        session: IngestionService, 
        renderer: RenderService,
        kb_service: KBService
    ) -> None:
        self.io = io
        self.session = session
        self.renderer = renderer
        self.kb_service = kb_service

    def run(self) -> str:
        try:
            action_res = self._bootstrap()
        except UserDecline:
            return ProgramExit.MSG_DECLINED_BOOTSTRAP        
        except NoConfig:
            try:
                self.io.get_confirmation(UserQuestions.INIT_REPO, UserQuestions.REQUIRED_PHRASE)
                self.session.initialize_workspace()
                action_res = self._bootstrap()
            except UserDecline:
                return ProgramExit.MSG_DECLINED_INIT
        except Exception as other_ex:
            return ExceptionPolicy.interpret_as_fatal(other_ex)

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
            return ProgramExit.MSG_DEFAULT
        except Exception as other_ex:
            return ExceptionPolicy.interpret_as_fatal(other_ex)

    def _bootstrap(self) -> ActionResult:
        action_res, report, btn_map, ui_render, base_resolvers = self.session.get_runtime_config()
        self.renderer.set_ui_render(ui_render)
        self.kb_service.setup(btn_map, base_resolvers)
        complaints = report.get_complaints()
        if complaints:
            self.io.get_confirmation(
                UserQuestions.complaints_proceed(complaints),
                UserQuestions.REQUIRED_PHRASE
            )
        return action_res