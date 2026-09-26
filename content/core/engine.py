#!/usr/bin/env -S python3 -B
from core import (
    ActionResult,
    UserQuestions,
    UserDecline,
    NoConfig,
    ProgramExit,
    HotPromptRequested,
    DoBootstrap,
    OfferBootstrapWithComplaints,
    OfferClankerize,
    OfferClankerizeWithComplaints,
    TerminateGracefully
)
from core.engine_deps import IngestionService, KBService, RenderService, TUIService

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
        action_res, report, btn_map, ui_render, base_resolvers = self.session.get_runtime_config()

        match action_res:
            case DoBootstrap():
                self.renderer.set_ui_render(ui_render)
                self.kb_service.setup(btn_map, base_resolvers)
                action_res = ActionResult(ActionResult.BOOTSTRAP_SUCCESS)

            case OfferBootstrapWithComplaints():
                try:
                    self.io.get_confirmation(
                        UserQuestions.complaints_proceed(report.get_complaints()),
                        UserQuestions.REQUIRED_PHRASE,
                    )
                except UserDecline:
                    return ActionResult.MSG_DECLINED_BOOTSTRAP
                self.renderer.set_ui_render(ui_render)
                self.kb_service.setup(btn_map, base_resolvers)
                action_res = ActionResult(ActionResult.BOOTSTRAP_SUCCESS)

            case OfferClankerize():
                try:
                    self.io.get_confirmation(
                        UserQuestions.INIT_REPO, UserQuestions.REQUIRED_PHRASE
                    )
                    self.session.initialize_workspace()
                    action_res, report, btn_map, ui_render, base_resolvers = self.session.get_runtime_config()
                    self.renderer.set_ui_render(ui_render)
                    self.kb_service.setup(btn_map, base_resolvers)
                    action_res = ActionResult(ActionResult.BOOTSTRAP_SUCCESS)
                except UserDecline:
                    return ActionResult.MSG_DECLINED_INIT

            case OfferClankerizeWithComplaints():
                try:
                    self.io.get_confirmation(
                        UserQuestions.complaints_proceed(report.get_complaints()),
                        UserQuestions.REQUIRED_PHRASE,
                    )
                    self.io.get_confirmation(
                        UserQuestions.INIT_REPO, UserQuestions.REQUIRED_PHRASE
                    )
                    self.session.initialize_workspace()
                    action_res, report, btn_map, ui_render, base_resolvers = self.session.get_runtime_config()
                    self.renderer.set_ui_render(ui_render)
                    self.kb_service.setup(btn_map, base_resolvers)
                    action_res = ActionResult(ActionResult.BOOTSTRAP_SUCCESS)
                except UserDecline:
                    return ActionResult.MSG_DECLINED_INIT

            case TerminateGracefully():
                all_crits = report.get_critical_complaints()
                all_softs = report.get_complaints()
                msg = "Critical errors:\n" + "\n".join(all_crits)
                if all_softs:
                    msg += "\nSoft complaints:\n" + "\n".join(all_softs)
                return msg

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