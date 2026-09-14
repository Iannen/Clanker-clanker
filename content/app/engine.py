#!/usr/bin/env -S python3 -B
from __future__ import annotations 
from enum import Enum
import os
from pathlib import Path
import copy
import sys
import traceback
from typing import Callable, ClassVar, Any
from app.models import *
from app.deps import *

class ExceptionPolicy:
    ADOPTED_NOTICES: tuple[type[Exception], ...] = (  
        FileNotFoundError,
        PermissionError,
        UnicodeDecodeError
    )

    @classmethod
    def protect_adapter(cls, adapter: Any) -> Any:
        def _wrap(fn):
            def wrapper(*args, **kwargs):
                try:
                    return fn(*args, **kwargs)
                except (Notice, *cls.ADOPTED_NOTICES):
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
        elif isinstance(ex, (Notice, *cls.ADOPTED_NOTICES)):
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
        renderer: RenderService
    ) -> None:
        self.io = io
        self.session = session
        self.renderer = renderer
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
                self.msg = self.kb.handle_key(cmd_key)
        except ProgramExit:
            return ProgramExit.MSG_DEFAULT
        except Exception as other_ex:
            return ExceptionPolicy.interpret_as_fatal(other_ex)

    def _bootstrap(self) -> ActionResult:
        report, rtc = self.session.get_runtime_config()
        dof_report = report.get_domain_overflow_report()
        if dof_report is not None:
            self.io.get_confirmation(
                f"{dof_report}\nDo you wish to proceed with overflowed domains trimmed?",
                required_phrase="yes"
            )
        self.runtime_config = rtc
        self.kb = self.runtime_config.keyboard
        self._wire_num_row()
        self._set_selected_num_btn(None)
        return ActionResult("Bootstrap completed successfully")

    def _wire_num_row(self) -> None:
        for btn in self.kb.get_unique_buttons(Button.TYPE_DOMAIN):
            btn.action = self._set_selected_num_btn

    def _set_selected_num_btn(self, key: str | None) -> ActionResult:
        if key is None:
            case = "none"
        else:
            ref_btn = self.kb.button_map[key]
            if ref_btn.type != Button.TYPE_DOMAIN:
                raise ValueError("Selected button is not a number button")
            case = "empty" if ref_btn.inhabitant is None else "inhabited"

        self.kb.selected_key = key
        prompt_btns = self.kb.get_unique_buttons(Button.TYPE_PROMPT)

        for b in prompt_btns:
            b.inhabitant = b.action = None

        if case == "inhabited":
            for p_btn, prompt in zip(prompt_btns, ref_btn.inhabitant.prompts):
                p_btn.inhabitant = prompt
                p_btn.action = self._compile_to_clipboard

            return ActionResult(f"Domain '{ref_btn.inhabitant.name}' on key '{key}' selected")

        msg = "Selection cleared" if case == "none" else f"Domain 'None' on key '{key}' selected"
        return ActionResult(msg)

    def _display_ui(self) -> str:
        self.io.display(self._render(self.runtime_config, self.runtime_config.ui_render))
        return self.io.get_key()

    def _compile_to_clipboard(self, key: str) -> ActionResult:
        btn = self.kb.button_map.get(key)
        if btn is None or btn.inhabitant is None or not isinstance(btn.inhabitant, Prompt):
            return ActionResult(f"No prompt assigned to key '{key}'")
        rendered_text = self._render(self.runtime_config, btn.inhabitant.render)
        lines_count = self.io.to_clipboard(rendered_text)
        char_count = len(rendered_text)
        return ActionResult(f"Copied {lines_count} lines ({char_count} chars) to clipboard")

    def _render(self, cfg: RuntimeConfig, render: Render):
        template = self.renderer.get_template(render)
        repl_map = self.renderer.get_repl_map(cfg, render)
        repl_map["msg"] = self.msg.get_msg()
        return self.renderer.hydrate(template, repl_map)