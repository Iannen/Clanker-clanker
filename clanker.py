#!/usr/bin/env python3
from __future__ import annotations
import base64
from enum import Enum
from ruamel.yaml import YAML
import os
from pathlib import Path
import re
import sys
import termios
import traceback
import tty
from typing import Callable, ClassVar, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator

""" 1. Templates, Default Configs & UI Strings """

DEFAULT_PROMPT_TEMPLATE = r"""
<runtime : kindly oblige if noobject>
  <msg-from-runtime-author kindly serve the function of the runtime>
    <document-tag fragment: base_instruction>
§base_instruction§
    </document-tag>
    <document-tag fragment: domain_instruction>
§domain_instruction§
    </document-tag>
    <document-tag fragment: prompt_instruction>
§prompt_instruction§
    </document-tag>
    <document-tag fragment: backlog>
§backlog§
    </document-tag>
    <document-tag fragment: repo_content>
§repo_content§
    </document-tag>
  </msg-from-runtime-author>
</runtime>"""

DEFAULT_BACKLOG_TEMPLATE = r"""
I. Long term goals

II. Medium term goals

III. Immediate goals
      - Explore the nature of the current repository. 
      - Is it new? Then bootstrap a new project
      - Does it have content? Then analyze with user

IV. Idea bucket:

V. Known Bugs

HISTORY STASH (insert below)

I: Initialized .clank directory 
    - ran clanker in repo directory
"""

MAIN_CONSOLE_TEMPLATE = r"""
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                         │
│    § 10   §  § 20   §  § 30   §  § 40   §  § 50   §  § 60   §  § 70   §  § 80   §  § 90   §  § 00   §                   │
│    § 11   §  § 21   §  § 31   §  § 41   §  § 51   §  § 61   §  § 71   §  § 81   §  § 91   §  § 01   §                   │
│    § 12   §  § 22   §  § 32   §  § 42   §  § 52   §  § 62   §  § 72   §  § 82   §  § 92   §  § 02   §                   │
│    § 13   §  § 23   §  § 33   §  § 43   §  § 53   §  § 63   §  § 73   §  § 83   §  § 93   §  § 03   §                   │
│    § 14   §  § 24   §  § 34   §  § 44   §  § 54   §  § 64   §  § 74   §  § 84   §  § 94   §  § 04   §                   │
│                                                                                                                         │
│     § q0   §  § w0   §  § e0   §  § r0   §                                                                              │
│     § q1   §  § w1   §  § e1   §  § r1   §                                                                              │
│     § q2   §  § w2   §  § e2   §  § r2   §                                                                              │
│     § q3   §  § w3   §  § e3   §  § r3   §                                                                              │
│     § q4   §  § w4   §  § e4   §  § r4   §                                                                              │
│                                                                                                                         │
│      § a0   §  § s0   §  § d0   §  § f0   §                                                                             │
│      § a1   §  § s1   §  § d1   §  § f1   §                                                                             │
│      § a2   §  § s2   §  § d2   §  § f2   §                                                                             │
│      § a3   §  § s3   §  § d3   §  § f3   §                                                                             │
│      § a4   §  § s4   §  § d4   §  § f4   §                                                                             │
│                                                                                                                         │
│                                                                                                                         │
│                                                                                                                         │
│                                                                                                                         │
│                                                                                                                         │
│                                                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
"""

HIGHLIGHTED_BTN = r"""
 vvvvvv 
┌──────┐
│  §   │
└──────┘
 §§§§§§ 
"""
ACTIVE_BTN = r"""
        
┌──────┐
│  §   │
└──────┘
 §§§§§§ 
"""
INACTIVE_BTN = r"""
        
        
   §    
────────
 §§§§§§ 
"""

CLANK_CONFIG_YAML = r"""
kb_def: 
    render: 
      name: "ui"
      template: "ui_template"
      inherit_base: false
      inherit_domain: false
      resolvers:
        - { id: "ui", type: "kb_info" }
    resolvers:
      - { id: "base_instruction", type: "document-retrieval", file: "general-rules.md" }
    rows:
      domain_row:
        primary: "1234567890"
        secondary: '!"#¤%&/()='
      prompt_row:
        primary: "qwer"
        secondary: "QWER"
      action_row:
        primary: "asdf"
        secondary: "ASDF"

domains:
- name: "script-dev"
  plan: 
    name: "script_development_plan"
  resolvers:
    - { id: "domain_instruction", type: "document-retrieval", file: "domain-script-dev.md" }
  renders:
    - name: 'script-dev'
      template: "prompt_template"
      resolvers:
        - { id: "prompt_instruction", type: "document-retrieval", file: "script_dev_instructions.md" }
        - { id: "backlog", type: "document-retrieval", file: "backlog.md" }
        - { id: "repo_content", type: "repo_content", includes: ["clanker.py"], excludes: [], sorting: "normal" }

- name: "config-dev"
  plan: 
    name: "config_development_plan"
  resolvers:
    - { id: "domain_instruction", type: "document-retrieval", file: "domain-config-dev.md" }
  renders:
    - name: 'config-dev'
      template: "prompt_template"
      resolvers:
        - { id: "prompt_instruction", type: "document-retrieval", file: "config-development-instructions.md" }
        - { id: "backlog", type: "document-retrieval", file: "backlog.md" }
        - { id: "repo_content", type: "repo_content", includes: ["clanker.py"], excludes: [], sorting: "normal" }

- name: "debloat"
  plan: 
    name: "debloat_plan"
  resolvers:
    - { id: "domain_instruction", type: "document-retrieval", file: "domain-debloat.md" }
  renders:
    - name: 'debloat'
      template: "prompt_template"
      resolvers:
        - { id: "prompt_instruction", type: "document-retrieval", file: "debloat-instructions.md" }
        - { id: "backlog", type: "document-retrieval", file: "backlog.md" }
        - { id: "repo_content", type: "repo_content", includes: ["clanker.py"], excludes: [], sorting: "normal" }
"""

CLANK_CONFIG = YAML().load(CLANK_CONFIG_YAML)

DEFAULT_CONFIG = r"""
kb_def: 
    render: 
      name: "ui"
      template: "ui_template"
      resolvers:
        - { id: "ui", type: "kb_info" }
    resolvers:
      - { id: "base_instruction", type: "document-retrieval", file: "general-rules.md" }
    rows:
      domain_row:
        primary: "1234567890"
        secondary: '!"#¤%&/()='
      prompt_row:
        primary: "qwer"
        secondary: "QWER"
      action_row:
        primary: "asdf"
        secondary: "ASDF"

domains:
- name: "bootstrap"
  plan: 
    name: "bootstrap_plan"
  resolvers:
    - { id: "domain_instruction", type: "document-retrieval", file: "domain-bootstrap.md" }
  renders:
    - name: 'bootstrap'
      template: "prompt_template"
      resolvers:
        - { id: "prompt_instruction", type: "document-retrieval", file: "bootstrap-instructions.md" }
        - { id: "backlog", type: "document-retrieval", file: "backlog.md" }
        - { id: "repo_content", type: "repo_content", includes: ["."], excludes: [".clanker"], sorting: "normal" }
"""

DEFAULT_CONFIG = YAML().load(DEFAULT_CONFIG)

""" 2. Base Classes & Main function """

class BaseAppEx(Exception):
    def __new__(cls, *args, **kwargs):
        if cls is BaseAppEx:
            raise BaseExInstantiationAttempt(cls.__name__)
        if cls is BaseNoticeEx and (args or kwargs):
            raise IllegalNoticeArgs(cls.__name__)
        return super().__new__(cls)
    ADOPTED_NOTICES: tuple[type[Exception], ...] = ( 
        FileNotFoundError,
        PermissionError
    )

    @classmethod
    def wrap_bridge_call(cls, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except cls.ADOPTED_NOTICES:
            raise
        except BaseNoticeEx:
            raise
        except Exception as ex:
            raise BridgeLeakageFailure() from ex

    @classmethod
    def reraise_as_failure(cls, ex: Exception) -> None:
        if isinstance(ex, BaseFailureEx):
            raise
        if isinstance(ex, BaseNoticeEx):
            raise MissedNoticeFailure(f"Missed notice: {ex}") from ex
        if isinstance(ex, BaseAppEx.ADOPTED_NOTICES):
            raise UncaughtAdoptedNoticeFailure(f"Adopted notice failure: [{type(ex).__name__}] {ex}") from ex
        else:
            raise UncaughtUnexpectedFailure(f"[{type(ex).__name__}] {ex}") from ex

    @classmethod
    def print_traceback_and_exit(cls, ex: Exception) -> None:
        cause = getattr(ex, "__cause__", None)
        err_detail = str(ex) if str(ex) else ex.__class__.__name__
        sys.stderr.write(f"\n[FAILURE] {err_detail}\n")
        if cause:
            sys.stderr.write("\n--- Underlying Stack Trace ---\n")
            traceback.print_exception(type(cause), cause, cause.__traceback__)
        sys.exit(1)

class BaseFailureEx(BaseAppEx): pass
class BaseNoticeEx(BaseAppEx): pass

class Engine:
    def run(self) -> str:
        try:
            bootstrap_res_msg = self._bootstrap_application()
            self._add_to_board(bootstrap_res_msg)
            while True:
                cmd_key = self._display_ui_to_user() 
                cmd_res_msg = self._dispatch_cmd(cmd_key)
                self._add_to_board(cmd_res_msg)
        except ProgramExitNotice as exit_request:
            return exit_request.get_compliance_msg()
        except Exception as any_other_ex:
            BaseAppEx.reraise_as_failure(any_other_ex)

class Bridge:
    def __init_subclass__(cls):
        for attr_name, attr_value in list(cls.__dict__.items()):
            if callable(attr_value) and not attr_name.startswith("_"):
                setattr(cls, attr_name, cls._wrap_safely(attr_value))
    @staticmethod
    def _wrap_safely(fn):
        def wrapper(*args, **kwargs):
            return BaseAppEx.wrap_bridge_call(fn, *args, **kwargs)
        return wrapper

class Constructed(BaseModel):
    model_config = ConfigDict(extra="forbid")

def main():
    try:
        files = FileBridge()
        io_bridge = IOBridge()

        session = SessionService()
        io = IOService()
        renderer = OutputAssemblyService()

        session.files = files
        io.io_bridge = io_bridge
        renderer.files = files

        engine = GameEngine()
        engine.io = io
        engine.session = session
        engine.renderer = renderer

        exit_msg = engine.run()
        print(exit_msg)
    except BaseFailureEx as ex:
        BaseAppEx.print_traceback_and_exit(ex)

""" 3. Exceptions, Result Objects, Enums """

class ActionResultMsg:
    def __init__(self, message: str):
        self.message = message

class MissedNoticeFailure(BaseFailureEx): pass
class BaseExInstantiationAttempt(BaseFailureEx): pass
class IllegalNoticeArgs(BaseFailureEx): pass
class BridgeLeakageFailure(BaseFailureEx): pass
class NotImplementedFailure(BaseFailureEx): pass
class UncaughtAdoptedNoticeFailure(BaseFailureEx): pass
class UncaughtUnexpectedFailure(BaseFailureEx): pass


class UserCancelNotice(BaseNoticeEx): pass
class UserDeclineNotice(BaseNoticeEx): pass
class BootstrapDeclineNotice(BaseNoticeEx): pass
class ProgramExitNotice(BaseNoticeEx):
    def get_compliance_msg(self):
        return "Program exited"
class NoConfigNotice(BaseNoticeEx): pass

class SystemKeys(Enum):  
    DELIM = "§"
    CTRL_C = "\x03"
    CTRL_D = "\x04"
    BACKSPACE = "\x7f"
    BACKSPACE_ALT = "\x08"
    ESC = "\x1b"

""" 4. App Abstractions (Models & Engine) """

class Plan(Constructed):
    name: str = ""

class Render(Constructed):
    name: str
    template: str
    resolvers: list[Resolver] = []
    inherit_base: bool = True
    inherit_domain: bool = True

class Domain(Constructed):
    name: str
    plan: Plan | None = None
    renders: list[Render] = []
    resolvers: list[Resolver] = []

class Config(Constructed):
    DEFAULT_REL_PATH: ClassVar[Path] = Path(".clanker/config.yaml")
    DEFAULT_ASSETS_DIR: ClassVar[Path] = Path(".clanker/assets")

    layout: str
    domains: list[str]

class Resolver(BaseModel):
    class Type(str, Enum):
        DOCUMENT_RETRIEVAL = "document-retrieval"
        REPO_CONTENT = "repo_content"
        KB_INFO = "kb_info"
    id: str
    type: Type
    payload: dict[str, Any] = {}

    @model_validator(mode="before")
    @classmethod
    def extract_payload(cls, data: Any) -> Any:
        if isinstance(data, dict):
            raw = data.copy()
            res_id = raw.pop("id", "")
            res_type = raw.pop("type", None)
            return {
                "id": res_id,
                "type": res_type,
                "payload": raw
            }
        return data

class Button(Constructed):
    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True  
    )
    type: str 
    primary_letter: str
    secondary_letter: str
    inhabitant: Domain | Render | None = None
    primary_action: Callable | None = None
    shift_action: Callable | None = None

    def get_repl_map(self, label: str, template: str) -> dict[str, str]:
        lines = template.strip("\n").splitlines()
        norm_label = (label + "      ")[:6]
        token = SystemKeys.DELIM.value
        
        mapped_lines = [
            lines[0],
            lines[1],
            lines[2].replace(token, self.primary_letter, 1),
            lines[3],
            lines[4].replace(token * 6, norm_label, 1),
        ]
        return {f"{self.primary_letter}{idx}": line for idx, line in enumerate(mapped_lines)}

class Keyboard(Constructed):
    CONFIGS_DIR: ClassVar[Path] = Path(".clanker/configs")
    button_map: dict[str, Button] = Field(default_factory=dict)
    render: Render 
    resolvers: list[Resolver] = []
    selected_num_btn_primary_letter: str | None = None

    def get_unique_buttons(self, btn_type: str | None = None) -> list[Button]:
        unique = {btn.primary_letter: btn for btn in self.button_map.values()}.values()
        if btn_type is None:
            return list(unique)
        return [btn for btn in unique if btn.type == btn_type]

    def handle_key(self, key: str) -> ActionResultMsg | None:
        btn = self.button_map.get(key)
        if btn is None:
            return None
        if key == btn.primary_letter and callable(btn.primary_action):
            return btn.primary_action(btn.primary_letter)
        elif key == btn.secondary_letter and callable(btn.shift_action):
            return btn.shift_action(btn.primary_letter)
        return ActionResultMsg(f"No action bound to key '{key}'")

    def build_ui_repl_map(self) -> dict[str, str]:
        repl_map = {}
        for btn in self.get_unique_buttons():
            label = ""
            template = INACTIVE_BTN
            if btn.type == "num_btn":
                if btn.primary_letter == self.selected_num_btn_primary_letter:
                    template = HIGHLIGHTED_BTN
                    label = btn.inhabitant.name if btn.inhabitant else ""
                elif btn.inhabitant:
                    template = ACTIVE_BTN
                    label = btn.inhabitant.name

            elif btn.type == "prompt_btn":
                if btn.inhabitant:
                    template = ACTIVE_BTN
                    label = btn.inhabitant.name

            elif btn.type == "action_btn":
                if btn.inhabitant:
                    template = ACTIVE_BTN
                    label = getattr(btn.inhabitant, "name", str(btn.inhabitant))

            repl_map |= btn.get_repl_map(label, template)
        return repl_map

class GameEngine(Engine):
    def _bootstrap_application(self) -> ActionResultMsg:
        try:
            self.kb = self.session.get_keyboard()
            self._wire_num_row_handlers()
            self._set_selected_num_btn(None)
            return ActionResultMsg("Bootstrap completed successfully")
        except NoConfigNotice:
            try:
                self.io.get_confirmation("Directory not initialized as clank repo - do so?")
                self.session.initialize_workspace()
                return self._bootstrap_application()
            except UserDeclineNotice:
                raise ProgramExitNotice
    def _dispatch_cmd(self, key: str) -> ActionResultMsg:
        return self.kb.handle_key(key)

    def _add_to_board(self, msg: ActionResultMsg | None) -> None:
        self.msg = msg

    def _wire_num_row_handlers(self) -> None:
        for btn in self.kb.get_unique_buttons("num_btn"):
            btn.primary_action = self._set_selected_num_btn
            btn.shift_action = lambda k: exec("raise NotImplementedError")

    def _set_selected_num_btn(self, key: str | None) -> ActionResultMsg:
        if key is None:
            case = "none"
        else:
            ref_btn = self.kb.button_map[key]
            if ref_btn.type != "num_btn":
                raise ValueError("Selected button is not a number button")
            case = "empty" if ref_btn.inhabitant is None else "inhabited"

        self.kb.selected_num_btn_primary_letter = key
        prompt_btns = self.kb.get_unique_buttons("prompt_btn")
        action_btns = self.kb.get_unique_buttons("action_btn")

        if case == "inhabited":
            for p_btn, prompt in zip(prompt_btns, ref_btn.inhabitant.renders):
                p_btn.inhabitant = prompt
                p_btn.primary_action = self._compile_prompt_to_clipboard
                p_btn.shift_action = lambda k: exec("raise NotImplementedError")

            for a_btn in action_btns:
                a_btn.primary_action = a_btn.shift_action = lambda k: exec("raise NotImplementedError")

            return ActionResultMsg(f"Domain '{ref_btn.inhabitant.name}' on key '{key}' selected")

        for b in prompt_btns + action_btns:
            b.inhabitant = b.primary_action = b.shift_action = None

        msg = "Selection cleared" if case == "none" else f"Domain 'None' on key '{key}' selected"
        return ActionResultMsg(msg)

    def _display_ui_to_user(self) -> str:
        view_str = self._render(self.kb, self.kb.render)
        self.io.display(view_str)
        return self.io.get_key()

    def _compile_prompt_to_clipboard(self, key: str) -> ActionResultMsg:
        btn = self.kb.button_map.get(key)
        if btn is None or btn.inhabitant is None:
            return ActionResultMsg(f"No prompt assigned to key '{key}'")
        compiled_prompt = self._render(self.kb, btn.inhabitant)
        lines_count = self.io.pushtoclipboard(compiled_prompt)
        return ActionResultMsg(f"Copied {lines_count} lines to clipboard")

    def _render(self, kb: Keyboard, render: Render):
        template = self.renderer.get_template(render)
        repl_map = self.renderer.get_repl_map(kb, render)
        return self.renderer.hydrate(template, repl_map)

""" 5. Services """

class SessionService:
    def get_keyboard(self) -> Keyboard:
        raw_yaml = self._get_raw_config()

        kb_def = raw_yaml["kb_def"]
        rows = kb_def["rows"]
        raw_domains = raw_yaml["domains"]

        parsed_domains = [Domain.model_validate(domain) for domain in raw_domains]

        button_map = {}

        for row_key, row in rows.items():
            btn_type = (
                "num_btn"
                if row_key == "domain_row"
                else ("prompt_btn" if row_key == "prompt_row" else "action_btn")
            )

            primary_keys = row["primary"]
            secondary_keys = row["secondary"]

            for prim, sec in zip(primary_keys, secondary_keys):
                btn_obj = Button(
                    type=btn_type,
                    primary_letter=prim,
                    secondary_letter=sec,
                    inhabitant=None,
                )
                button_map[prim] = btn_obj
                button_map[sec] = btn_obj

        domain_primaries = rows["domain_row"]["primary"]

        for idx, domain_obj in enumerate(parsed_domains):
            if idx < len(domain_primaries):
                prim_char = domain_primaries[idx]
                button_map[prim_char].inhabitant = domain_obj

        return Keyboard.model_validate(
            {
                "button_map": button_map,
                "render": kb_def["render"],
                "resolvers": kb_def.get("resolvers"),
            }
        )

    def is_cwd_script_dir(self) -> bool:
        return self.files.is_cwd_script_dir()

    def _get_raw_config(self) -> dict:
        try:
            return self.files.read_yaml(Config.DEFAULT_REL_PATH)
        except FileNotFoundError:
            raise NoConfigNotice

    def initialize_workspace(self) -> None:
        config = CLANK_CONFIG if self.files.is_cwd_script_dir() else DEFAULT_CONFIG
        self.files.write_yaml(Config.DEFAULT_REL_PATH, config)
        
        backlog_path = Config.DEFAULT_ASSETS_DIR / "backlog.md"
        self.files.write_content(backlog_path, DEFAULT_BACKLOG_TEMPLATE)

class OutputAssemblyService:
    BUILTIN_TEMPLATES: ClassVar[dict[str, str]] = {
        "prompt_template": DEFAULT_PROMPT_TEMPLATE,
        "ui_template": MAIN_CONSOLE_TEMPLATE,
    }
    def hydrate(self, template: str, replacements: dict[str, str]) -> str:
        token = SystemKeys.DELIM.value
        pattern = re.compile(rf"{token}([^{token}]+){token}")
        return pattern.sub(
            lambda m: replacements.get(m.group(1).strip(), m.group(0)),
            template
        )

    def get_template(self, render: Render) -> str:
        asset_path = Config.DEFAULT_ASSETS_DIR / render.template
        try:
            return self.files.read_content(asset_path)
        except (FileNotFoundError, OSError):
            return self.BUILTIN_TEMPLATES[render.template]

    def get_repl_map(self, keyboard: Keyboard, render: Render) -> dict[str, str]:
        active_resolvers: list[Resolver] = []
        if render.inherit_base:
            active_resolvers.extend(keyboard.resolvers)
        if render.inherit_domain and keyboard.selected_num_btn_primary_letter:
            active_btn = keyboard.button_map.get(keyboard.selected_num_btn_primary_letter)
            if active_btn and isinstance(active_btn.inhabitant, Domain):
                active_resolvers.extend(active_btn.inhabitant.resolvers)
        active_resolvers.extend(render.resolvers)
        replacements: dict[str, str] = {}
        for resolver in active_resolvers:
            for key, val in self._resolve(resolver, keyboard):
                replacements[key] = val
        return replacements

    def _resolve(self, resolver: Resolver, keyboard: Keyboard) -> list[tuple[str, str]]:
        if resolver.type == Resolver.Type.DOCUMENT_RETRIEVAL:
            filename = resolver.payload.get("file")
            if not filename:
                raise ValueError(f"Resolver '{resolver.id}' missing 'file' payload")
            asset_path = Config.DEFAULT_ASSETS_DIR / filename
            try:
                content = self.files.read_content(asset_path)
            except FileNotFoundError:
                content = f"[{resolver.id}: No content found at '{filename}']"
            return [(resolver.id, content)]

        if resolver.type == Resolver.Type.REPO_CONTENT:
            includes = resolver.payload.get("includes", [])
            excludes = resolver.payload.get("excludes", [])
            included = self.files.expand_paths(includes)
            excluded = self.files.expand_paths(excludes)
            paths = sorted(included - excluded)

            tree_header = "\n".join(f"├── {p}" for p in paths)
            file_blocks = [f"--- {p} ---\n{self.files.read_content(p)}" for p in paths]
            content = f"{tree_header}\n\n" + "\n\n".join(file_blocks)
            return [(resolver.id, content)]

        if resolver.type == Resolver.Type.KB_INFO:
            return list(keyboard.build_ui_repl_map().items())

        raise ValueError(f"Unsupported resolver type: {resolver.type}")

class IOService: 
    def display(self, ui_string: str) -> None:
        self.io_bridge.clear()
        self.io_bridge.write(f"{ui_string}\n")

    def pushtoclipboard(self, text_content: str) -> int:
        return self.io_bridge.pushtoclipboard(text_content)

    def get_key(self) -> str:
        ch = self.io_bridge.read_char()
        if ch in (SystemKeys.CTRL_C.value, SystemKeys.ESC.value):
            raise ProgramExitNotice
        return ch

    def get_confirmation(self, prompt_msg: str, required_phrase: str = "") -> None:
        self.io_bridge.write(f"\n{prompt_msg}\n")
        if required_phrase:
            self.io_bridge.write(
                f"Type '{required_phrase}' and press [Ctrl+D] to confirm, or [ESC/Ctrl+C] to cancel.\n"
            )
        else:
            self.io_bridge.write("Press [Ctrl+D] to confirm, or [ESC/Ctrl+C] to cancel.\n")

        self.io_bridge.write("> ")
        buffer = ""

        while True:
            ch = self.io_bridge.read_char()

            if ch in (SystemKeys.CTRL_C.value, SystemKeys.ESC.value):
                raise UserDeclineNotice

            if ch == SystemKeys.CTRL_D.value:
                if buffer == required_phrase:
                    self.io_bridge.write("\n")
                    return None
                self.io_bridge.write(
                    f"\nInvalid confirmation. Expected '{required_phrase}'. Try again.\n> "
                )
                buffer = ""
            elif ch in (SystemKeys.BACKSPACE.value, SystemKeys.BACKSPACE_ALT.value):
                if len(buffer) > 0:
                    buffer = buffer[:-1]
                    self.io_bridge.write("\b \b")
            elif ch.isprintable():
                buffer += ch
                self.io_bridge.write(ch)

""" 6. Bridge """

class IOBridge(Bridge): 
    def clear(self) -> None:
        os.system("clear")

    def pushtoclipboard(self, text_content: str) -> int:
        payload = base64.b64encode(text_content.encode("utf-8")).decode("utf-8")
        sys.stdout.write(f"\033]52;c;{payload}\007")
        sys.stdout.flush()
        return len(text_content.splitlines())

    def write(self, text: str) -> None:
        print(text, end="", flush=True)

    def read_char(self) -> str:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

class FileBridge(Bridge):
    def __init__(self) -> None:
        self.yaml = YAML()
        self.base_path = Path.cwd()

    def read_yaml(self, rel_path: Path) -> dict:
        with open(self.base_path / rel_path, "r", encoding="utf-8") as f:
            return self.yaml.load(f)

    def is_cwd_script_dir(self) -> bool:
        return self.base_path.resolve() == Path(__file__).parent.resolve()
    
    def write_yaml(self, rel_path: Path, data: dict) -> None:
        target_path = self.base_path / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            self.yaml.dump(data, f)

    def read_content(self, rel_path: Path) -> str:
        with open(self.base_path / rel_path, "r", encoding="utf-8") as f:
            return f.read()

    def write_content(self, rel_path: Path, content: str) -> None:
        target_path = self.base_path / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)

    def expand_paths(self, rel_roots: list[str | Path]) -> set[Path]:
        resolved_files: set[Path] = set()
        base_dir = self.base_path

        for root_str in rel_roots:
            rel_path = Path(root_str)
            full_path = base_dir / rel_path

            if not full_path.exists():
                raise FileNotFoundError(rel_path)

            if full_path.is_file():
                resolved_files.add(rel_path)
            elif full_path.is_dir():
                for file_path in full_path.rglob("*"):
                    if file_path.is_file():
                        resolved_files.add(file_path.relative_to(base_dir))

        return resolved_files

""" 7. Script Entrypoint """

if __name__ == "__main__":
    main()