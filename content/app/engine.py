#!/usr/bin/env -S python3 -B
import traceback
from typing import Callable, Any
from app.presentation import ActionResult
from app.exceptions import UserDecline, NoConfig, Fatal, Notice, UnexpectedEx, BaseEx, ProgramExit, MissedNotice
from app.deps import *
from app.entities import Button, Prompt
from app.deps.keyboard import KBService

class ExceptionPolicy:
    @classmethod
    def protect_adapter(cls, adapter: Any) -> Any:
        def _wrap(fn):
            def wrapper(*args, **kwargs):
                try:
                    return fn(*args, **kwargs)
                except BaseEx:
                    raise
                except Exception as ex:
                    raise AdapterLeakage() from ex
            return wrapper

        wrapped = {
            name: _wrap(getattr(adapter, name))
            for name in dir(adapter)
            if not name.startswith("_") and callable(getattr(adapter, name))
        }

        for name, fn in wrapped.items():
            setattr(adapter, name, fn)

        return adapter

    @classmethod
    def interpret_as_fatal(cls, ex: Exception) -> str:
        if isinstance(ex, Fatal):
            fatal_ex = ex
        elif isinstance(ex, Notice):
            fatal_ex = MissedNotice(f"Missed notice: {ex.__class__.__name__}")
            fatal_ex.__cause__ = ex
        else:
            fatal_ex = UnexpectedEx(f"[{type(ex).__name__}] {ex}")
            fatal_ex.__cause__ = ex

        msg_parts = [f"\n[FATAL] {type(fatal_ex).__name__}{fatal_ex}\n"]

        cause = getattr(fatal_ex, "__cause__", None)
        if cause is not None:
            msg_parts.append("\n--- Underlying Stack Trace ---\n")
            msg_parts.append("".join(traceback.format_exception(type(cause), cause, cause.__traceback__)))
        elif fatal_ex.__traceback__ is not None:
            msg_parts.append("".join(traceback.format_exception(type(fatal_ex), fatal_ex, fatal_ex.__traceback__)))

        return "".join(msg_parts)

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
        self.msg: ActionResult | None = None

    def run(self) -> str:
        try:
            self.msg = self._bootstrap()
        except UserDecline:
            return ProgramExit.MSG_DECLINED_BOOTSTRAP        
        except NoConfig:
            try:
                self.io.get_confirmation("Directory not initialized as clank repo - clankerize?", "yes")
                self.session.initialize_workspace()
                self.msg = self._bootstrap()
            except UserDecline:
                return ProgramExit.MSG_DECLINED_INIT
        except Exception as other_ex:
            return ExceptionPolicy.interpret_as_fatal(other_ex)

        try:
            while True:
                cmd_key = self._display_ui()
                ar, render_ctx = self.kb_service.handle_key(cmd_key)
                if ar is not None:
                    self.msg = ar
                elif render_ctx is not None:
                    # i think perhaps a next step could be to reduce the calls to RenderService in one public render_prompt method or similar
                    template = self.renderer.get_template(render_ctx.render)
                    repl_map = self.renderer.get_repl_map(render_ctx.keyboard, render_ctx.base_resolvers, render_ctx.render)
                    repl_map["msg"] = self.msg.get_msg() if self.msg is not None else ""
                    rendered_text = self.renderer.hydrate(template, repl_map)
                    # i think TUIService should return the actionresult here - so engine dont need to doctor it up
                    lines_count = self.io.to_clipboard(rendered_text)
                    char_count = len(rendered_text)
                    self.msg = ActionResult(f"Copied {lines_count} lines ({char_count} chars) to clipboard")
        except ProgramExit:
            return ProgramExit.MSG_DEFAULT
        except Exception as other_ex:
            return ExceptionPolicy.interpret_as_fatal(other_ex)

    def _bootstrap(self) -> ActionResult:
        report, keyboard, ui_render, base_resolvers = self.session.get_runtime_config()
        dof_report = report.get_domain_overflow_report()
        if dof_report is not None:
            self.io.get_confirmation(
                f"{dof_report}\nDo you wish to proceed with overflowed domains trimmed?",
                required_phrase="yes"
            )
        complaints = report.get_complaints()
        if complaints:
            self.io.get_confirmation(
                f"{"\n".join(complaints)}\nProceed anyway?",
                required_phrase="yes"
            )
        self.kb = keyboard
        self.ui_render = ui_render
        self.base_resolvers = base_resolvers
        self.renderer.set_ui_render(ui_render)
        self.kb_service.setup(keyboard, base_resolvers)
        return ActionResult("Bootstrap completed successfully")
    # perhaps we can inline this at callsite, its a small thing. extract it into self render call, then self io display call, then io get key call, inline at callsite
    def _display_ui(self) -> str:
        self.io.display(self.renderer.render_ui(self.kb, self.msg))
        return self.io.get_key()