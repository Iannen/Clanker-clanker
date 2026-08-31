#!/usr/bin/env python3
from __future__ import annotations
from enum import Enum
import os
from pathlib import Path
import re
import sys
import traceback
import copy
from typing import Callable, ClassVar, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator
from abc import ABC, abstractmethod

""" 2. Base Classes & Main function """

class BaseEx(Exception):
    def __new__(cls, *args, **kwargs):
        if cls is BaseEx:
            raise BaseExInstantiation(cls.__name__)
        if cls is Notice and (args or kwargs):
            raise NoticeArgs(cls.__name__)
        return super().__new__(cls)
    ADOPTED_NOTICES: tuple[type[Exception], ...] = ( 
        FileNotFoundError,
        PermissionError,
        UnicodeDecodeError
    )

    @classmethod
    def wrap_bridge_call(cls, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except cls.ADOPTED_NOTICES:
            raise
        except Notice:
            raise
        except Exception as ex:
            raise BridgeLeakage() from ex

    @classmethod
    def reraise_as_failure(cls, ex: Exception) -> None:
        if isinstance(ex, Failure):
            raise
        if isinstance(ex, Notice):
            raise MissedNotice(f"Missed notice: {ex}") from ex
        if isinstance(ex, BaseEx.ADOPTED_NOTICES):
            raise MissedAdoptedNotice(f"Adopted notice failure: [{type(ex).__name__}] {ex}") from ex
        else:
            raise UnexpectedEx(f"[{type(ex).__name__}] {ex}") from ex

    @classmethod
    def print_traceback_and_exit(cls, ex: Exception) -> None:
        cause = getattr(ex, "__cause__", None)
        err_detail = str(ex) if str(ex) else ex.__class__.__name__
        sys.stderr.write(f"\n[FAILURE] {err_detail}\n")
        if cause:
            sys.stderr.write("\n--- Underlying Stack Trace ---\n")
            traceback.print_exception(type(cause), cause, cause.__traceback__)
        sys.exit(1)

class Failure(BaseEx): pass
class Notice(BaseEx): pass

class Engine:
    def run(self) -> str:
        try:
            self._add_to_board(self._bootstrap())
            while True:
                cmd_key = self._display_ui()
                cmd_res_msg = self._dispatch_cmd(cmd_key)
                self._add_to_board(cmd_res_msg)
        except ProgramExit as exit_request:
            return exit_request.get_compliance_msg()
        except Exception as other_ex:
            BaseEx.reraise_as_failure(other_ex)

class Bridge(ABC):
    def __init_subclass__(cls):
        for attr_name, attr_value in list(cls.__dict__.items()):
            if callable(attr_value) and not attr_name.startswith("_"):
                setattr(cls, attr_name, cls._wrap_safely(attr_value))
    @staticmethod
    def _wrap_safely(fn):
        def wrapper(*args, **kwargs):
            return BaseEx.wrap_bridge_call(fn, *args, **kwargs)
        return wrapper

class Constructed(BaseModel):
    model_config = ConfigDict(extra="forbid")

def main():
    try:
        from adapters import FileBridge, IOBridge

        # Instantiate Adapters
        files_adapter = FileBridge()
        io_adapter = IOBridge()

        # Inject into Services
        session = SessionService(files=files_adapter)
        renderer = AssemblyService(files=files_adapter)
        io = IOService(io_bridge=io_adapter)

        # Inject into Engine
        engine = GameEngine(
            io=io,
            session=session,
            renderer=renderer
        )

        exit_msg = engine.run()
        print(exit_msg)
    except Failure as ex:
        BaseEx.print_traceback_and_exit(ex)

""" 3. Exceptions, Result Objects, Enums """

class CfgFragments:
    PUD_CFG = ".clanker/config.yaml"
    SHARED_KB_DEF = ".clanker/shared-assets/config-fragments/kb_def.yaml"
    SHARED_DOMAINS = ".clanker/shared-assets/config-fragments/shared_domains.yaml"
    TEMPLATE_CFG = ".clanker/shared-assets/templates/config.template"
    
class DocPaths:
    SHARED_TEMPLATES = ".clanker/shared-assets/templates/documentation"
    PUD_DOCS = ".clanker/progress-documentation"
    TEMPL_EXT = ".template"
    DOC_EXT = ".cdoc"

class Layout:
    UI = ".clanker/shared-assets/layouts/ui.layout"
    PROMPT = ".clanker/shared-assets/layouts/prompt.layout"
    BTN_ACTIVE = ".clanker/shared-assets/layouts/btn_active.layout"
    BTN_HL = ".clanker/shared-assets/layouts/btn_hl.layout"
    BTN_INACTIVE = ".clanker/shared-assets/layouts/btn_inactive.layout"

class SystemKeys:
    DELIM = "§"
    CTRL_C = "\x03"
    CTRL_D = "\x04"
    BACKSPACE = "\x7f"
    BACKSPACE_ALT = "\x08"
    ESC = "\x1b"

class ActionResult:
    def __init__(self, message: str):
        self.message = message

    def get_msg(self) -> str:
        width = 117
        return f"{self.message:<{width}}"[:width]

class MissedNotice(Failure): pass
class BaseExInstantiation(Failure): pass
class NoticeArgs(Failure): pass
class BridgeLeakage(Failure): pass
class BadFile(Failure): pass
class NotImplemented(Failure): pass
class MissedAdoptedNotice(Failure): pass
class UnexpectedEx(Failure): pass
class CorruptClanker(Failure): pass
class ConfigAssemblyFailure(Failure): pass
class IllegalDuplicateFile(Failure): pass

class UserDecline(Notice): pass
class ProgramExit(Notice):
    def get_compliance_msg(self):
        return "Program exited"
class NoConfig(Notice): pass

""" 4. App Abstractions (Models & Engine) """

class Render(Constructed):
    name: str
    template: str = "prompt_template"
    resolvers: list[Resolver] = []
    inherit_base: bool = True
    inherit_domain: bool = True

class Domain(Constructed):
    name: str
    renders: list[Render] = []
    resolvers: list[Resolver] = []

class Config(Constructed):
    DEFAULT_REL_PATH: ClassVar[Path] = Path(".clanker/config.yaml")
    DEFAULT_ASSETS_DIR: ClassVar[Path] = Path(".clanker/assets")
    layout: str
    domains: list[str]

class Resolver(BaseModel):
    class Type(str, Enum):
        MULTI_DOC = "multi-document-retrieval"
        FULL_PATH_FILE = "full-path-file-retrieval"
        REPO_CONTENT = "repo_content"
        KB_INFO = "kb_info"
    id: str
    type: Type
    payload: dict[str, Any] = {}

    @model_validator(mode="before")
    @classmethod
    def extract_payload(cls, data: Any) -> Any:
        if isinstance(data, dict):
            obj_id = data.get("id", "")
            obj_type = data.get("type", None)
            payload = {k: v for k, v in data.items() if k not in ("id", "type")}
            return {
                "id": obj_id,
                "type": obj_type,
                "payload": payload
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
        norm_label = (label + "     ")[:6]

        mapped_lines = [
            lines[0],
            lines[1],
            lines[2].replace(SystemKeys.DELIM, self.primary_letter, 1),
            lines[3],
            lines[4].replace(SystemKeys.DELIM * 6, norm_label, 1),
        ]
        return {f"{self.primary_letter}{idx}": line for idx, line in enumerate(mapped_lines)}

class Keyboard(Constructed):
    button_map: dict[str, Button] = Field(default_factory=dict)
    render: Render 
    resolvers: list[Resolver] = []
    selected_key: str | None = None

    def get_unique_buttons(self, btn_type: str | None = None) -> list[Button]:
        unique = {btn.primary_letter: btn for btn in self.button_map.values()}.values()
        if btn_type is None:
            return list(unique)
        return [btn for btn in unique if btn.type == btn_type]

    def handle_key(self, key: str) -> ActionResult | None:
        btn = self.button_map.get(key)
        if btn is None:
            return None
        if key == btn.primary_letter and callable(btn.primary_action):
            return btn.primary_action(btn.primary_letter)
        elif key == btn.secondary_letter and callable(btn.shift_action):
            return btn.shift_action(btn.primary_letter)
        return ActionResult(f"No action bound to key '{key}'")

class GameEngine(Engine):
    def __init__(
        self, 
        io: IOService, 
        session: SessionService, 
        renderer: AssemblyService
    ) -> None:
        self.io = io
        self.session = session
        self.renderer = renderer
    def _bootstrap(self) -> ActionResult:
        try:
            self.kb = self.session.get_keyboard()
            self._wire_num_row()
            self._set_selected_num_btn(None)
            return ActionResult("Bootstrap completed successfully")
        except NoConfig:
            try:
                self.io.get_confirmation("Directory not initialized as clank repo - do so?")
                self.session.initialize_workspace()
                return self._bootstrap()
            except UserDecline:
                raise ProgramExit
    def _dispatch_cmd(self, key: str) -> ActionResult:
        return self.kb.handle_key(key)

    def _add_to_board(self, msg: ActionResult | None) -> None:
        self.msg = msg

    def _wire_num_row(self) -> None:
        for btn in self.kb.get_unique_buttons("domain_row"):
            btn.primary_action = self._set_selected_num_btn
            btn.shift_action = lambda k: exec("raise NotImplementedError")

    def _set_selected_num_btn(self, key: str | None) -> ActionResult:
        if key is None:
            case = "none"
        else:
            ref_btn = self.kb.button_map[key]
            if ref_btn.type != "domain_row":
                raise ValueError("Selected button is not a number button")
            case = "empty" if ref_btn.inhabitant is None else "inhabited"

        self.kb.selected_key = key
        prompt_btns = self.kb.get_unique_buttons("prompt_row")
        action_btns = self.kb.get_unique_buttons("action_row")

        for b in prompt_btns + action_btns:
            b.inhabitant = b.primary_action = b.shift_action = None

        if case == "inhabited":
            for p_btn, prompt in zip(prompt_btns, ref_btn.inhabitant.renders):
                p_btn.inhabitant = prompt
                p_btn.primary_action = self._compile_to_clipboard
                p_btn.shift_action = lambda k: exec("raise NotImplementedError")

            for a_btn in action_btns:
                a_btn.primary_action = a_btn.shift_action = lambda k: exec("raise NotImplementedError")

            return ActionResult(f"Domain '{ref_btn.inhabitant.name}' on key '{key}' selected")

        msg = "Selection cleared" if case == "none" else f"Domain 'None' on key '{key}' selected"
        return ActionResult(msg)

    def _display_ui(self) -> str:
        self.io.display(self._render(self.kb, self.kb.render))
        return self.io.get_key()

    def _compile_to_clipboard(self, key: str) -> ActionResult:
        btn = self.kb.button_map.get(key)
        if btn is None or btn.inhabitant is None:
            return ActionResult(f"No prompt assigned to key '{key}'")
        rendered_text = self._render(self.kb, btn.inhabitant)
        lines_count = self.io.to_clipboard(rendered_text)
        char_count = len(rendered_text)
        return ActionResult(f"Copied {lines_count} lines ({char_count} chars) to clipboard")

    def _render(self, kb: Keyboard, render: Render):
        template = self.renderer.get_template(render)
        repl_map = self.renderer.get_repl_map(kb, render)
        repl_map["msg"] = self.msg.get_msg()
        return self.renderer.hydrate(template, repl_map)

""" 5. Services """

class SessionService:
    def __init__(self, files: FileBridgePort) -> None:
        self.files = files

    def get_keyboard(self) -> Keyboard:
        try:
            config_data = self.files.pud_cfg_frag(CfgFragments.PUD_CFG)
        except FileNotFoundError:
            raise NoConfig

        try:
            kb_def_data = self.files.clank_cfg_frag(CfgFragments.SHARED_KB_DEF)
            
            shared_domains = []
            shared_sets = {}
            try:
                shared_domains_data = self.files.clank_cfg_frag(CfgFragments.SHARED_DOMAINS)
                shared_domains = shared_domains_data.get("domains", [])
                shared_sets = shared_domains_data.get("sets", {})
            except FileNotFoundError:
                pass
        except FileNotFoundError as ex:
            raise ConfigAssemblyFailure(f"Missing configuration fragment: {ex}") from ex
        except Exception as ex:
            if isinstance(ex, Failure):
                raise
            raise ConfigAssemblyFailure(f"Failed to assemble configuration: {ex}") from ex

        sets_map = {**shared_sets, **config_data.get("sets", {})}
        user_domains = config_data.get("domains", [])
        combined_domains = shared_domains + user_domains
        resolved_domains = self._resolve_sets(combined_domains, sets_map)

        raw_yaml = {**kb_def_data, **config_data}
        raw_yaml["domains"] = resolved_domains

        button_map = {}
        for row_key, row in raw_yaml["kb_def"]["rows"].items():
            for prim, sec in zip(row["primary"], row["secondary"]):
                button_map[prim] = button_map[sec] = Button(
                    type=row_key, primary_letter=prim, secondary_letter=sec, inhabitant=None
                )

        for prim_char, d in zip(raw_yaml["kb_def"]["rows"]["domain_row"]["primary"], raw_yaml["domains"]):
            button_map[prim_char].inhabitant = Domain.model_validate(d)

        return Keyboard.model_validate({
            "button_map": button_map,
            "render": raw_yaml["kb_def"]["render"],
            "resolvers": raw_yaml["kb_def"].get("resolvers"),
        })

    def _resolve_sets(self, node: Any, sets_map: dict[str, Any]) -> Any:
        if isinstance(node, list):
            return [self._resolve_sets(item, sets_map) for item in node]
        elif isinstance(node, dict):
            res_copy = node.copy()
            pointer_key = res_copy.pop("varname", None)
            if pointer_key is None:
                pointer_key = res_copy.pop("set", None)
            if pointer_key and pointer_key in sets_map:
                set_val = sets_map[pointer_key]
                if isinstance(set_val, dict):
                    #res_copy.update(set_val)
                    res_copy.update(copy.deepcopy(set_val))
            return {k: self._resolve_sets(v, sets_map) for k, v in res_copy.items()}
        return node

    def initialize_workspace(self) -> None:
        if self.files.is_cwd_script_dir():
            raise CorruptClanker("Clanker repository initialized is beyond scope of app.")

        try:
            default_config_data = self.files.clank_cfg_frag(CfgFragments.TEMPLATE_CFG)
        except FileNotFoundError as ex:
            raise ConfigAssemblyFailure(f"Missing configuration template: {ex}") from ex
        except Exception as ex:
            if isinstance(ex, Failure):
                raise
            raise ConfigAssemblyFailure(f"Failed to load configuration template: {ex}") from ex

        self.files.write_yaml(Config.DEFAULT_REL_PATH, default_config_data)

        self.files.write_default_documents(
            doc_templ_dir=DocPaths.SHARED_TEMPLATES,
            pud_doc_dir=DocPaths.PUD_DOCS,
            templ_ext=DocPaths.TEMPL_EXT,
            doc_ext=DocPaths.DOC_EXT
        )

class AssemblyService:
    def __init__(self, files: FileBridgePort) -> None:
        self.files = files

    def hydrate(self, template: str, replacements: dict[str, str]) -> str:
        token = SystemKeys.DELIM
        pattern = re.compile(rf"{token}([^{token}]+){token}")
        return pattern.sub(
            lambda m: replacements.get(m.group(1).strip(), m.group(0)),
            template
        )

    def get_template(self, render: Render) -> str:
        match render.template:
            case "prompt_template":
                layout_path = Layout.PROMPT
            case "ui_template":
                layout_path = Layout.UI
        try:
            return self.files.read_clanker_asset(layout_path)
        except FileNotFoundError as ex:
            raise CorruptClanker(f"Error: Layout '{layout_path}': {ex}") from ex

    def get_repl_map(self, keyboard: Keyboard, render: Render) -> dict[str, str]:
        active_resolvers: list[Resolver] = []
        if render.inherit_base:
            active_resolvers.extend(keyboard.resolvers)
        if render.inherit_domain:
            active_btn = keyboard.button_map.get(keyboard.selected_key)
            if active_btn and isinstance(active_btn.inhabitant, Domain):
                active_resolvers.extend(active_btn.inhabitant.resolvers)
        active_resolvers.extend(render.resolvers)
        replacements: dict[str, str] = {}
        for resolver in active_resolvers:
            for key, val in self._resolve(resolver, keyboard):
                replacements[key] = val
        return replacements


    def _resolve(self, resolver: Resolver, keyboard: Keyboard) -> list[tuple[str, str]]:

        if resolver.type == Resolver.Type.MULTI_DOC:
            fragments = []
            asset_map = self.files.getAssetMap()

            for item in resolver.payload.get("files", []):
                if isinstance(item, dict):
                    filename = item.get("file", "")
                    tail_lines = item.get("tail_lines")
                else:
                    filename = item
                    tail_lines = None

                basename = Path(filename).name
                target_path = asset_map.get(basename)
                
                if target_path:
                    content = self.files.getFileContent(target_path)
                    if tail_lines is not None:
                        lines = content.splitlines()
                        if len(lines) > tail_lines:
                            content = "**truncated**\n" + "\n".join(lines[-tail_lines:])
                else:
                    content = f"[{resolver.id}: No content found at '{filename}']"
                    
                fragments.append(f"<{basename}>\n{content}\n</{basename}>")
                
            return [(resolver.id, "\n\n".join(fragments))]

        if resolver.type == Resolver.Type.FULL_PATH_FILE:
            fragments = []

            for item in resolver.payload.get("files", []):
                if isinstance(item, dict):
                    filename = item.get("file", "")
                    tail_lines = item.get("tail_lines")
                else:
                    filename = item
                    tail_lines = None

                rel_path = Path(filename)
                try:
                    content = self.files.read_pud_asset(rel_path)
                    if tail_lines is not None:
                        lines = content.splitlines()
                        if len(lines) > tail_lines:
                            content = "**truncated**\n" + "\n".join(lines[-tail_lines:])
                except FileNotFoundError:
                    content = f"[{resolver.id}: No content found at '{filename}']"

                fragments.append(f"<{filename}>\n{content}\n</{filename}>")

            return [(resolver.id, "\n\n".join(fragments))]

        if resolver.type == Resolver.Type.REPO_CONTENT:
            paths = sorted(
                self.files.get_pud_files(resolver.payload.get("includes", [])) - 
                self.files.get_pud_files(resolver.payload.get("excludes", []))
            )
            
            tree_header = f"<tree>\n" + "\n".join(f"├── {p}" for p in paths) + "\n</tree>"
            
            file_blocks = []
            for p in paths:
                try:
                    content = self.files.read_pud_asset(p).rstrip()  
                    file_blocks.append(f"<{p}>\n{content}\n</{p}>")
                except UnicodeDecodeError:
                    pass

            inner_content = tree_header + "\n" + "\n".join(file_blocks)
            return [(resolver.id, f"<repo-content>\n{inner_content}\n</repo-content>")]

        if resolver.type == Resolver.Type.KB_INFO:
            btn_hl = self.files.read_clanker_asset(Layout.BTN_HL)
            btn_active = self.files.read_clanker_asset(Layout.BTN_ACTIVE)
            btn_inactive = self.files.read_clanker_asset(Layout.BTN_INACTIVE)

            repl_map = {}
            for btn in keyboard.get_unique_buttons():
                label = ""
                template = btn_inactive
                if btn.type == "domain_row":
                    if btn.primary_letter == keyboard.selected_key:
                        template = btn_hl
                        label = btn.inhabitant.name if btn.inhabitant else ""
                    elif btn.inhabitant:
                        template = btn_active
                        label = btn.inhabitant.name

                elif btn.type == "prompt_row":
                    if btn.inhabitant:
                        template = btn_active
                        label = btn.inhabitant.name

                elif btn.type == "action_row":
                    if btn.inhabitant:
                        template = btn_active
                        label = getattr(btn.inhabitant, "name", str(btn.inhabitant))

                repl_map |= btn.get_repl_map(label, template)
            return list(repl_map.items())

        raise ValueError(f"Unsupported resolver type: {resolver.type}")

class IOService:
    def __init__(self, io_bridge: IOBridgePort) -> None:
        self.io_bridge = io_bridge

    def display(self, ui_string: str) -> None:
        self.io_bridge.clear()
        self.io_bridge.write(f"{ui_string}\n")

    def to_clipboard(self, text_content: str) -> int:
        return self.io_bridge.to_clipboard(text_content)

    def get_key(self) -> str:
        ch = self.io_bridge.read_char()
        if ch in (SystemKeys.CTRL_C, SystemKeys.ESC):
            raise ProgramExit
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

            if ch in (SystemKeys.CTRL_C, SystemKeys.ESC):
                raise UserDecline

            if ch == SystemKeys.CTRL_D:
                if buffer == required_phrase:
                    self.io_bridge.write("\n")
                    return None
                self.io_bridge.write(
                    f"\nInvalid confirmation. Expected '{required_phrase}'. Try again.\n> "
                )
                buffer = ""
            elif ch in (SystemKeys.BACKSPACE, SystemKeys.BACKSPACE_ALT):
                if len(buffer) > 0:
                    buffer = buffer[:-1]
                    self.io_bridge.write("\b \b")
            elif ch.isprintable():
                buffer += ch
                self.io_bridge.write(ch)

""" 6. Bridge Ports"""

class IOBridgePort(Bridge):

    @abstractmethod
    def clear(self) -> None: pass

    @abstractmethod
    def to_clipboard(self, text_content: str) -> int: pass

    @abstractmethod
    def write(self, text: str) -> None: pass

    @abstractmethod
    def read_char(self) -> str: pass

class FileBridgePort(Bridge):

    @abstractmethod
    def pud_cfg_frag(self, rel_path: str) -> dict: pass

    @abstractmethod
    def clank_cfg_frag(self, rel_path: str) -> dict: pass

    @abstractmethod
    def write_default_documents(
        self, doc_templ_dir: str, pud_doc_dir: str, templ_ext: str, doc_ext: str
    ) -> None: pass

    @abstractmethod
    def is_cwd_script_dir(self) -> bool: pass

    @abstractmethod
    def write_yaml(self, rel_path: Path, data: dict) -> None: pass

    @abstractmethod
    def read_clanker_asset(self, rel_path: str) -> str: pass

    @abstractmethod
    def read_pud_asset(self, rel_path: Path) -> str: pass

    @abstractmethod
    def write_content(self, rel_path: Path, content: str) -> None: pass

    @abstractmethod
    def get_pud_files(self, rel_roots: list[str | Path]) -> set[Path]: pass

    @abstractmethod
    def getAssetMap(self) -> dict[str, Path]: pass

    @abstractmethod
    def getFileContent(self, full_path: Path | str) -> str: pass

""" 7. Script Entrypoint """

if __name__ == "__main__":
    main()