#!/usr/bin/env python3
from __future__ import annotations
import base64
from enum import Enum, StrEnum
from ruamel.yaml import YAML
import os
from pathlib import Path
import re
import sys
import termios
import traceback
import tty
from typing import Callable, ClassVar
from pydantic import BaseModel, ConfigDict, Field

""" 1. Templates, Default Configs & UI Strings """

DEFAULT_PROMPT_TEMPLATE = r"""
<runtime : kindly oblige if noobject>
  <msg-from-runtime-author kindly serve the function of the runtime>
    <document-tag fragment: general_rules>
§general_rules§
    </document-tag>
    <document-tag fragment: script_dev>
§script_dev§
    </document-tag>
    <document-tag fragment: script_file_only>
§script_file_only§
    </document-tag>
  </msg-from-runtime-author>
</runtime>"""

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
active_num_btn: "1"
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
  - name: "Main script"
    plan: null
    prompts:
      - name: "config-dev"
        symbol_set: &default_symbols
          indent: "  "
          arrow_indent: "=>"
          open_tag: "<{tag} {attr}>"
          open_tag_no_attr: "<{tag}>"
          closed_tag: "</{tag}>"
          self_closing_tag: "<{tag} {attr} />"
          self_closing_no_attr: "<{tag} />"
        prompt_fragments:
          - id: "general_rules"
            type: "document"
            path: ".clanker/assets/general-rules.md"
          - id: "config_development"
            type: "document"
            path: ".clanker/assets/config_development_instructions.md"
          - id: "script_file_only"
            type: "file_set"
            resolver:
              sorter: "path_asc"
              inclusion_roots: ["clanker.py"]
              exclusion_roots: []

      - name: "script-dev"
        symbol_set: *default_symbols
        prompt_fragments:
          - id: "general_rules"
            type: "document"
            path: ".clanker/assets/general-rules.md"
          - id: "script_dev"
            type: "document"
            path: ".clanker/assets/script_dev_instructions.md"
          - id: "script_file_only"
            type: "file_set"
            resolver:
              sorter: "path_asc"
              inclusion_roots: ["clanker.py"]
              exclusion_roots: []

      - name: "debloat"
        symbol_set: *default_symbols
        prompt_fragments:
          - id: "general_rules"
            type: "document"
            path: ".clanker/assets/general-rules.md"
          - id: "debloat"
            type: "document"
            path: ".clanker/assets/debloat_instructions.md"
          - id: "script_file_only"
            type: "file_set"
            resolver:
              sorter: "path_asc"
              inclusion_roots: ["clanker.py"]
              exclusion_roots: []
"""

CLANK_CONFIG = YAML().load(CLANK_CONFIG_YAML)


DEFAULT_CONFIG = {
    "active_num_btn": "1",
    "rows": {
        "domain_row": {"primary": "1234567890", "secondary": '!"#¤%&/()='},
        "prompt_row": {"primary": "qwer", "secondary": "QWER"},
        "action_row": {"primary": "asdf", "secondary": "ASDF"}
    },
    "domains": []
}

""" 2. Base Classes & Main function """

class BaseAppEx(Exception):

    def __new__(cls, *args, **kwargs):
        if cls is BaseAppEx:
            raise BaseExInstantiationAttempt(cls.__name__)
        if cls is BaseNoticeEx and (args or kwargs):
            raise IllegalNoticeArgs(cls.__name__)
        return super().__new__(cls)

    ADOPTED_NOTICES: tuple[type[Exception], ...] = ( # list would be prettier
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
                cmd_key = self._display_ui_to_user() # use pipeline method. we need contributors in scope.
                cmd_res_msg = self._dispatch_cmd(cmd_key)
                self._add_to_board(cmd_res_msg)
        except ProgramExitNotice as exit_request:
            return exit_request.get_compliance_msg()
        except Exception as any_other_ex:
            BaseAppEx.reraise_as_failure(any_other_ex)

    def _bootstrap_application(self) -> ActionResultMsg:
        raise NotImplementedError
    def _display_ui_to_user(self) -> str:
        raise NotImplementedError

    def _dispatch_cmd(self, key: str) -> ActionResultMsg:
        raise NotImplementedError
    def _add_to_board(self, msg: ActionResultMsg | None) -> None:
        raise NotImplementedError

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

class BaseStrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

def main():
    try:
        files = FileBridge()
        io_bridge = IOBridge()

        session = SessionService()
        kb = KeyboardService()
        io = IOService()
        renderer = OutputAssemblyService()

        session.files = files
        io.io_bridge = io_bridge
        kb.files = files
        renderer.files = files

        engine = GameEngine()
        engine.kb = kb
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

class Config(BaseStrictModel):
    DEFAULT_REL_PATH: ClassVar[Path] = Path(".clanker/config.yaml")
    DEFAULT_ASSETS_DIR: ClassVar[Path] = Path(".clanker/assets")

    active_num_btn: str = "1"
    rows: dict[str, dict[str, str]]
    domains: list[Domain] = []

class Domain(BaseStrictModel):
    name: str
    plan: Plan | None = None
    prompts: list[Prompt] = []

class Plan(BaseStrictModel):
    name: str = ""
    pass

class PromptFragment(BaseStrictModel):
    class Type(StrEnum):
        FILE_SET = "file_set"
        DOCUMENT = "document"
    id: str
    type: Type
    path: Path | None = None
    resolver: FileSetResolver | None = None

class Prompt(BaseStrictModel):
    name: str
    symbol_set: SymbolSet
    prompt_fragments: list[PromptFragment] = []

class SymbolSet(BaseStrictModel):
    indent: str
    arrow_indent: str
    open_tag: str
    open_tag_no_attr: str
    closed_tag: str
    self_closing_tag: str
    self_closing_no_attr: str

class FileSetResolver(BaseStrictModel):
    class Sorter(StrEnum):
        PATH_ASC = "path_asc"
        PATH_DESC = "path_desc"
        DEPENDENCY_GRAPH = "dependency_graph"

    sorter: Sorter = Sorter.PATH_ASC
    inclusion_roots: list[str] = []
    exclusion_roots: list[str] = []

class Button(BaseModel):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)
    type: str 
    primary_letter: str
    secondary_letter: str
    inhabitant: object | None = None
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

class GameEngine(Engine):

    def _bootstrap_application(self) -> ActionResultMsg:
        try:
            cfg = self.session.get_config()
            self.kb.build_button_map(cfg.rows)
            self.kb.populate_num_keys(cfg.domains)
            self.wire_num_row_handlers()
            self.set_selected_num_btn(cfg.active_num_btn)
            return ActionResultMsg("Bootstrap completed successfully")
        except NoConfigNotice:
            try:
                self.io.get_confirmation("Config missing. Create default config?")
                config = CLANK_CONFIG if self.session.is_cwd_script_dir() else DEFAULT_CONFIG
                self.session.save_config(config)
                return self._bootstrap_application()
            except UserDeclineNotice:
                raise ProgramExitNotice

    def _display_ui_to_user(self) -> str:
        repl_map = self.kb._build_ui_repl_map() | self.session._build_ui_repl_map()
        view_str = self.renderer.hydrate(MAIN_CONSOLE_TEMPLATE, repl_map)
        self.io.display(view_str)
        return self.io.get_key()

    def _dispatch_cmd(self, key: str) -> ActionResultMsg:
        return self.kb.handle_key(key)

    def _add_to_board(self, msg: ActionResultMsg | None) -> None:
        self.msg = msg

    def wire_num_row_handlers(self) -> None:
        for btn in self.kb.get_unique_buttons("num_btn"):
            btn.primary_action = lambda key: self.set_selected_num_btn(key)
            btn.shift_action = lambda key: exec("raise NotImplementedError")

    def set_selected_num_btn(self, key: str | None) -> ActionResultMsg:
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
            for p_btn, prompt in zip(prompt_btns, ref_btn.inhabitant.prompts):
                p_btn.inhabitant = prompt
                p_btn.primary_action = self.compile_prompt_to_clipboard
                p_btn.shift_action = lambda k: exec("raise NotImplementedError")

            for a_btn in action_btns:
                a_btn.primary_action = a_btn.shift_action = lambda k: exec("raise NotImplementedError")

            return ActionResultMsg(f"Domain '{ref_btn.inhabitant.name}' on key '{key}' selected")

        for b in prompt_btns + action_btns:
            b.inhabitant = b.primary_action = b.shift_action = None

        msg = "Selection cleared" if case == "none" else f"Domain 'None' on key '{key}' selected"
        return ActionResultMsg(msg)

    def compile_prompt_to_clipboard(self, key: str) -> ActionResultMsg:
        btn = self.kb.button_map.get(key)
        if btn is None or btn.inhabitant is None:
            return ActionResultMsg(f"No prompt assigned to key '{key}'")

        compiled_prompt = self.renderer.hydrate(
            DEFAULT_PROMPT_TEMPLATE, 
            self.renderer.get_repl_map(btn.inhabitant)
        )
        lines_count = self.io.pushtoclipboard(compiled_prompt)
        return ActionResultMsg(f"Copied {lines_count} lines to clipboard")

    def _display_frame_get_cmd_key(self, ui_frame: str) -> str:
        self.io.display(ui_frame)
        return self.io.get_key()

    def _execute_cmd(self, key: str) -> ActionResultMsg:
        return self._dispatch_cmd(key)

    def _process_res_object(self, msg: ActionResultMsg | None) -> None:
        self._add_to_board(msg)

""" 5. Services """

class SessionService:

    def get_unique_buttons(self, btn_type: str | None = None) -> list[Button]:
        unique = {btn.primary_letter: btn for btn in self.button_map.values()}.values()
        if btn_type is None:
            return list(unique)
        return [btn for btn in unique if btn.type == btn_type]

    def _build_button_map(self, rows: dict[str, dict[str, str]]) -> None:
            self.button_map = {}
            for row_key, row in rows.items():
                btn_type = (
                    "num_btn" if row_key == "domain_row"
                    else ("prompt_btn" if row_key == "prompt_row" else "action_btn")
                )

                for prim, sec in zip(row["primary"], row["secondary"]):
                    btn = Button(
                        type=btn_type,
                        primary_letter=prim,
                        secondary_letter=sec,
                    )
                    self.button_map[prim] = btn
                    self.button_map[sec] = btn

    def _populate_num_keys(self, domains: list[Domain]) -> None:
        for btn, domain in zip(self.get_unique_buttons("num_btn"), domains):
            btn.inhabitant = domain



    def is_cwd_script_dir(self) -> bool:
        return self.files.is_cwd_script_dir()

    
    def get_config(self) -> Config:
        try:
            raw_data = self.files.read_yaml(Config.DEFAULT_REL_PATH)
            return Config.model_validate(raw_data) 
        except FileNotFoundError:
            raise NoConfigNotice
    
    def save_config(self, raw_config: dict) -> None:
        config = Config.model_validate(raw_config)
        self.files.write_yaml(Config.DEFAULT_REL_PATH, config.model_dump(mode="json"))

    def _build_ui_repl_map(self) -> dict:
        return {"last_msg": "hello from ss"}

# new name proposal: CommandRouter
class KeyboardService:
    
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

    def _build_ui_repl_map(self) -> dict[str, str]:
        repl_map = {}
        for btn in self.get_unique_buttons():
            label = ""
            template = INACTIVE_BTN

            if btn.type == "num_btn":
                if btn.primary_letter == getattr(self, "selected_num_btn_primary_letter", None):
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
    
    def build_button_map(self, rows: dict[str, dict[str, str]]) -> None:
            self.button_map = {}
            for row_key, row in rows.items():
                btn_type = (
                    "num_btn" if row_key == "domain_row"
                    else ("prompt_btn" if row_key == "prompt_row" else "action_btn")
                )

                for prim, sec in zip(row["primary"], row["secondary"]):
                    btn = Button(
                        type=btn_type,
                        primary_letter=prim,
                        secondary_letter=sec,
                    )
                    self.button_map[prim] = btn
                    self.button_map[sec] = btn

    def populate_num_keys(self, domains: list[Domain]) -> None:
        for btn, domain in zip(self.get_unique_buttons("num_btn"), domains):
            btn.inhabitant = domain
    
class OutputAssemblyService:

    def hydrate(self, template: str, replacements: dict[str, str]) -> str:
        token = SystemKeys.DELIM.value
        pattern = re.compile(rf"{token}([^{token}]+){token}")
        return pattern.sub(
            lambda m: replacements.get(m.group(1).strip(), m.group(0)),
            template
        )
    def get_repl_map(self, prompt_config: Prompt) -> dict[str, str]:
        replacements: dict[str, str] = {
            fragment.id: self._resolve(fragment)
            for fragment in prompt_config.prompt_fragments
        }
        return replacements
        
    def _resolve(self, fragment: PromptFragment) -> str:
        if fragment.type == PromptFragment.Type.DOCUMENT:
            if not fragment.path:
                raise ValueError(f"Document fragment '{fragment.id}' missing path")
            return self.files.read_content(fragment.path)

        if fragment.type == PromptFragment.Type.FILE_SET:
            if not fragment.resolver:
                raise ValueError(f"File set fragment '{fragment.id}' missing resolver")
            included = self.files.expand_paths(fragment.resolver.inclusion_roots)
            excluded = self.files.expand_paths(fragment.resolver.exclusion_roots)
            paths = sorted(included - excluded)

            tree_header = "\n".join(f"├── {p}" for p in paths)
            file_blocks = [f"--- {p} ---\n{self.files.read_content(p)}" for p in paths]
            return f"{tree_header}\n\n" + "\n\n".join(file_blocks)

        raise ValueError(f"Unsupported fragment type: {fragment.type}")

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