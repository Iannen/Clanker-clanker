#!/usr/bin/env python3
from __future__ import annotations
import json
import os
import re
import sys
import termios
import tty
from enum import Enum
from pathlib import Path
from typing import Callable, ClassVar
from pydantic import BaseModel, ConfigDict, Field


"""
TOC
    1. Exceptions result objects, enums 
    2. Application Core - Engine & subjects
    3. Services
    4. Bridge  
    5. String templates
    6. DI, Main and Entrypoint
"""

""" 1. Exceptions result objects, enums 
We never use defensive coding anywhere. we always use execptions, that we may declare for the purpose.
"""

class ActionResultMsg:
    def __init__(self, message: str):
        self.message = message

class BaseAppEx(Exception):
    ADOPTED_NOTICES: tuple[type[Exception], ...] = (FileNotFoundError, PermissionError)

    def __new__(cls, *args, **kwargs):
        cls._validate_instantiation(args, kwargs)
        return super().__new__(cls)
    @classmethod
    def _validate_instantiation(cls, args: tuple, kwargs: dict) -> None:
        if cls.__name__.startswith("Base"):
            raise BaseExInstantiationAttempt
        if args or kwargs:
            raise BaseExInstantiationAttempt

class BaseFailureEx(BaseAppEx): pass
class BaseNoticeEx(BaseAppEx): pass

class MissedNoticeFailure(BaseFailureEx): pass
class BaseExInstantiationAttempt(BaseFailureEx): pass
class BridgeLeakageFailure(BaseFailureEx): pass
class NotImplementedFailure(BaseFailureEx): pass
class UncaughtAdoptedNoticeFailure(BaseFailureEx): pass

class UserCancelNotice(BaseNoticeEx): pass
class UserDeclineNotice(BaseNoticeEx): pass
class BootstrapDeclineNotice(BaseNoticeEx): pass
class ProgramExitNotice(BaseNoticeEx): pass
class NoConfigNotice(BaseNoticeEx): pass

class SystemKeys(Enum):  
    DELIM = "§"
    CTRL_C = "\x03"
    CTRL_D = "\x04"
    BACKSPACE = "\x7f"
    BACKSPACE_ALT = "\x08"
    ESC = "\x1b"

""" 2. App abstractions
"""

class BaseStrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class Config(BaseStrictModel):
    DEFAULT_REL_PATH: ClassVar[Path] = Path(".clanker/config.json")

    active_num_btn: str = "1"
    rows: dict[str, dict[str, str]]
    domains: list[Domain] = []

class Plan(BaseStrictModel):
    name: str = ""
    pass
"""
    "symbols": {
        "indent": "  ",
        "arrow_indent": "=>",
        "open_tag": "<{tag} {attr}>",
        "open_tag_no_attr": "<{tag}>",
        "closed_tag": "</{tag}>",
        "self_closing_tag": "<{tag} {attr} />",
        "self_closing_no_attr": "<{tag} />",
    }
"""
class SymbolSet(BaseStrictModel):
    indent: str
    arrow_indent: str
    open_tag: str
    open_tag_no_attr: str
    closed_tag: str
    self_closing_tag: str
    self_closing_no_attr: str


class PromptFragment(BaseStrictModel):
    id: str
    type: str
    resolver: str

class Prompt(BaseStrictModel):
    name: str
    symbol_set: SymbolSet
    prompt_fragments: list[PromptFragment] = []


class Domain(BaseStrictModel):
    name: str
    plan: Plan | None = None
    prompts: list[Prompt] = []


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

class GameEngine:

    def bootstrap(self) -> "GameEngine":
        try:
            self.kb.load_config()
        except NoConfigNotice:
            try:
                self.io.get_confirmation("Config missing. Create default config?")
                raw_config = CLANK_CONFIG if self.session.is_cwd_script_dir() else DEFAULT_CONFIG
                self.kb.save_config(raw_config)
                self.kb.load_config()
            except UserDeclineNotice:
                raise BootstrapDeclineNotice

    def run(self) -> ActionResultMsg:
        try:
            self.bootstrap()
            self.action_result = ActionResultMsg('Bootstrap completed successfully') 
        except BootstrapDeclineNotice:
            return ActionResultMsg("Bootstrap cancelled by user")

        while True:
            try:
                repl_map = self.kb._build_ui_repl_map() | self.session._build_ui_repl_map()
                view_str = self.renderer.render_ui(MAIN_CONSOLE_TEMPLATE, repl_map) 
                self.io.display(view_str) 
                key = self.io.get_key() 
            except UserCancelNotice: 
                break
            except BaseNoticeEx as notice:
                raise MissedNoticeFailure from notice
            except BaseAppEx.ADOPTED_NOTICES as notice:
                raise UncaughtAdoptedNoticeFailure from notice
            except BaseFailureEx:
                raise
        return ActionResultMsg("Shutdown requested")

""" 3. Services """

class SessionService:
    def is_cwd_script_dir(self) -> bool:
        return self.files.is_cwd_script_dir()

    def _build_ui_repl_map(self) -> dict:
        return {"last_msg": "hello from ss"}

class KeyboardService:   

    def _build_ui_repl_map(self) -> dict[str, str]:
        repl_map = {}
        unique_buttons = {id(btn): btn for btn in self.button_map.values()}.values()
        for btn in unique_buttons:
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


    def load_config(self) -> None:
        try:
            raw_data = self.files.read_json(Config.DEFAULT_REL_PATH)
            config = Config.model_validate(raw_data)
        except FileNotFoundError:
            raise NoConfigNotice

        self.button_map = {}
        for row_key, row in config.rows.items():
            btn_type = (
                "num_btn" if row_key == "domain_row" 
                else ("prompt_btn" if row_key == "prompt_row" else "action_btn")
            )
            
            for prim, sec in zip(row["primary"], row["secondary"]):
                btn = Button(type=btn_type, primary_letter=prim, secondary_letter=sec)
                self.button_map[prim] = btn
                self.button_map[sec] = btn

        domain_primaries = config.rows["domain_row"]["primary"]
        for letter, domain in zip(domain_primaries, config.domains):
            self.button_map[letter].inhabitant = domain

        self._set_selected_num_btn(config.active_num_btn)

    def save_config(self, raw_config: dict) -> None:
        config = Config.model_validate(raw_config)
        self.files.write_json(Config.DEFAULT_REL_PATH, config.model_dump())

    def _set_selected_num_btn(self, btn_primary: str | None) -> None:
        self.selected_num_btn_primary_letter = btn_primary
        prompt_buttons = [btn for btn in self.button_map.values() if btn.type == 'prompt_btn']

        if btn_primary is None or btn_primary not in self.button_map:
            self.selected_num_btn_primary_letter = None
            for btn in prompt_buttons:
                btn.inhabitant = None
            return

        referenced_btn = self.button_map[btn_primary]

        if referenced_btn.type != 'num_btn':
            raise ValueError("Selected button is not a number button")

        if referenced_btn.inhabitant is None:
            for btn in prompt_buttons:
                btn.inhabitant = None
        else:
            for prompt_btn, prompt in zip(prompt_buttons, referenced_btn.inhabitant.prompts):
                prompt_btn.inhabitant = prompt

class OutputAssemblyService:
    def _hydrate(self, template: str, replacements: dict[str, str]) -> str:
        token = SystemKeys.DELIM.value
        pattern = re.compile(rf"{token}([^{token}]+){token}")
        return pattern.sub(
            lambda m: replacements.get(m.group(1).strip(), m.group(0)),
            template
        )

    def build_prompt(self, prompt_config: Prompt) -> str:
        symbols = prompt_config.symbol_set

        replacements = {
            "testdoc": "talk like a pirate!"
        }

        prompt = (
            _PromptBuilder(symbols=symbols)
            .add_open_tag("runtime", attr=": kindly oblige if noobject")
                .add_open_tag("msg-from-runtime-author", attr="kindly serve the function of the runtime")
                .add_doc("document-tag", "testdoc", attr="will it work? arg ordering is wonky")
            .close_current_tag()
        )

        return self._hydrate(prompt.consume(), replacements)

    def render_ui(self, template: str, replacements: dict[str, str]) -> str:
        return self._hydrate(template, replacements)

class IOService: 
    def display(self, ui_string: str) -> None:
        self.io_bridge.clear()
        self.io_bridge.write(f"{ui_string}\n")

    def get_key(self) -> str:
        ch = self.io_bridge.read_char()
        if ch in (SystemKeys.CTRL_C.value, SystemKeys.ESC.value):
            raise UserCancelNotice
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

class _PromptBuilder:
    """Private helper for OutputAssemblyService utilizing SymbolSet domain model."""

    def __init__(self, symbols: SymbolSet):
        self.symbols = symbols
        self._lines: list[str] = []
        self._stack: list[str] = []

    def add_open_tag(self, tag: str, attr: str | None = None) -> _PromptBuilder:
        indent = self.symbols.indent * len(self._stack)
        tmpl = self.symbols.open_tag if attr else self.symbols.open_tag_no_attr
        self._lines.append(f"{indent}{tmpl.format(tag=tag, attr=attr)}")
        self._stack.append(tag)
        return self

    def close_current_tag(self) -> _PromptBuilder:
        if self._stack:
            tag = self._stack.pop()
            indent = self.symbols.indent * len(self._stack)
            tmpl = self.symbols.closed_tag
            self._lines.append(f"{indent}{tmpl.format(tag=tag)}")
        return self

    def add_single_tag(self, tag: str, attr: str | None = None) -> _PromptBuilder:
        indent = self.symbols.indent * len(self._stack)
        tmpl = self.symbols.self_closing_tag if attr else self.symbols.self_closing_no_attr
        self._lines.append(f"{indent}{tmpl.format(tag=tag, attr=attr)}")
        return self

    def add_doc(self, tag: str, token_key: str, attr: str | None = None) -> _PromptBuilder:
        token = SystemKeys.DELIM.value
        self.add_open_tag(tag, attr)
        indent = self.symbols.indent * len(self._stack)
        self._lines.append(f"{indent}{token}{token_key}{token}")
        self.close_current_tag()
        return self

    def consume(self) -> str:
        while self._stack:
            self.close_current_tag()
        return "\n".join(self._lines)

""" 4. Bridge """

class Bridge:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for attr_name, attr_value in list(cls.__dict__.items()):
            if callable(attr_value) and not attr_name.startswith("_"):
                setattr(cls, attr_name, cls._wrap_safely(attr_value))

    @staticmethod
    def _wrap_safely(fn): 
    
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except BaseAppEx.ADOPTED_NOTICES:
                raise
            except BaseNoticeEx:
                raise
            except Exception as ex:
                raise BridgeLeakageFailure(f"Fatal bridge error in [{fn.__qualname__}]: {ex}") from ex
        return wrapper

class IOBridge(Bridge): 
    def clear(self) -> None:
        os.system("clear")

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

    def read_json(self, rel_path: Path) -> dict:
        target_path = self.base_path_provider() / rel_path 
        with open(target_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def is_cwd_script_dir(self) -> bool:
        return self.base_path_provider().resolve() == Path(__file__).parent.resolve()
    
    def write_json(self, rel_path: Path, data: dict) -> None:
        target_path = self.base_path_provider() / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


""" 5. String templates, defaults & similar """ 

MAIN_CONSOLE_TEMPLATE_OLD = r"""
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│ CLANKER CONTROL CONSOLE v1.0                                                                      │
├───────────────────────────────────────────────────────────────────────────────────────────────────┤
│  Domain specialists:                                                                              │
│  ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐                                      │
│  │ 1 │ │ 2 │ │ 3 │ │ 4 │ │ 5 │ │ 6 │ │ 7 │ │ 8 │ │ 9 │ │ 0 │                                      │
│  └───┘ └───┘ └───┘ └───┘ └───┘ └───┘ └───┘ └───┘ └───┘ └───┘                                      │
├───────────────────────────────────────────────────────┬───────────────────────────────────────────┤
│  KEY MATRIX                                           │ {ds_name}                                 │
│  ┌───┐ ┌───┐ ┌───┐ ┌───┐                              │ ───────────────────────────────────────── │
│  │ q │ │ w │ │ e │ │ r │                              │  q: {pr_q_name}                           │
│  └───┘ └───┘ └───┘ └───┘                              │  w: {pr_w_name}                           │
│    ┌───┐ ┌───┐ ┌───┐ ┌───┐                            │  e: {pr_e_name}                           │
│    │ a │ │ s │ │ d │ │ f │                            │  r: {pr_r_name}                           │
│    └───┘ └───┘ └───┘ └───┘                            │                                           │
├───────────────────────────────────────────────────────┼───────────────────────────────────────────┤
│ STATUS                                                │ CONSOLE OUTPUT / ASCII ART                │
│ ───────────────────────────────────────────────────── │ ───────────────────────────────────────── │
│  a: <not decided>      s: <not decided>               │                                           │
│  d: <not decided>      f: <not decided>               │                  \_\_                     │
│  ───────────────────────────────────────────────────  │               .-'   `-.                   │
│  Shift + A-F: Inspect Raw / Override                  │              /  .---. \                   │
│                                                       │             |  /     \ |                  │
│                                                       │             |  \     / |                  │
│                                                       │              \  `---' /                   │
│                                                       │               `-.____.-'                  │
├───────────────────────────────────────────────────────┴───────────────────────────────────────────┤
│ > {last_msg}                                                                                      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
""".lstrip('\n')

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

CLANK_CONFIG = {
    "active_num_btn": "1",
    "rows": {
        "domain_row": {"primary": "1234567890", "secondary": '!"#¤%&/()='},
        "prompt_row": {"primary": "qwer", "secondary": "QWER"},
        "action_row": {"primary": "asdf", "secondary": "ASDF"}
    },
    "domains": [
        {
            "name": "Main script",
            "plan": None,
            "prompts": [
                {
                    "name": "TaskRunnerPrompt",
                    "symbol_set": {
                        "indent": "  ",
                        "arrow_indent": "=>",
                        "open_tag": "<{tag} {attr}>",
                        "open_tag_no_attr": "<{tag}>",
                        "closed_tag": "</{tag}>",
                        "self_closing_tag": "<{tag} {attr} />",
                        "self_closing_no_attr": "<{tag} />"
                    },
                    "prompt_fragments": [
                        {
                            "id": "init_task",
                            "type": "doc",
                            "resolver": "default_resolver"
                        }
                    ]
                }
            ]
        }
    ]
}

DEFAULT_CONFIG = {
    "active_num_btn": "1",
    "rows": {
        "domain_row": {"primary": "1234567890", "secondary": '!"#¤%&/()='},
        "prompt_row": {"primary": "qwer", "secondary": "QWER"},
        "action_row": {"primary": "asdf", "secondary": "ASDF"}
    },
    "domains": []
}

""" 6. DI, Main and Entrypoint """

class InstanceFactory:
    def __init__(self):
        self.files = FileBridge()
        self.files.base_path_provider = lambda: Path.cwd()
        self.io_bridge = IOBridge()

        self.session = SessionService()
        self.session.files = self.files

        self.io = IOService()
        self.io.io_bridge = self.io_bridge

        self.kb = KeyboardService()
        self.kb.files = self.files

        self.renderer = OutputAssemblyService()

    def create_game_engine(self) -> GameEngine:
        engine = GameEngine()
        engine.kb = self.kb
        engine.io = self.io
        engine.session = self.session
        engine.renderer = self.renderer
        return engine

def main():
    try:
        engine = InstanceFactory().create_game_engine()
        exit_msg = engine.run()
        print(f"Byebye: {exit_msg.message}")
    except BaseFailureEx as ex:
        sys.stderr.write(f"Failure: {ex}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()

"""
Rules
    - i want discussion with competent counterpart on my terms
    - focus on what i want
    - never return code or script to me unsolicited.
    - you should always ask for clarification or seek resolution, and never be afraid to speak truth
output instructions
    - retain docstrings & pattern implied
    - do not introduce docstrings. any 
    - copyable markdown block to my spec. sometimes several in a row, other times full file.
    - never output code without explicit directive to do so
antipatterns:
    - unwarranted assignments in methods
        -> use available reference
    - defensive inline guarding
        -> update exception system 
    - wastefull empty lines 
""" 
"""

## when running ##
make domain switching work.
then make prompt gen buttons work.
adapt to my current workflow -> accelerating devving
"""