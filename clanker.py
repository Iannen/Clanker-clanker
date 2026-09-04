#!/usr/bin/env python3
from __future__ import annotations
from enum import Enum
import os
from pathlib import Path
import sys
import traceback
import copy
from typing import Callable, ClassVar, Any, Protocol
from abc import ABC, abstractmethod
from models import (
    Button,
    Config,
    Domain,
    Keyboard,
    Prompt,
    Render,
    Resolver,
    SystemKeys,
    RuntimeConfig,
)

""" 2. Base Classes & Main function """

class BaseEx(Exception):
    def __new__(cls, *args, **kwargs):
        if cls is BaseEx:
            raise BaseExInstantiation(cls.__name__)
        if cls is ControlNotice and (args or kwargs):
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
        except ControlNotice:
            raise
        except Exception as ex:
            raise BridgeLeakage() from ex

    @classmethod
    def reraise_as_failure(cls, ex: Exception) -> None:
        if isinstance(ex, Failure):
            raise
        if isinstance(ex, ControlNotice):
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
class ControlNotice(BaseEx): pass
class UserNotice(BaseEx): pass

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

def main():
    try:
        #file 'adapters.py'
        from adapters import FileBridge, IOBridge
        files_adapter = FileBridge()
        io_adapter = IOBridge()
        
        #file 'utilities.py'
        from utilities import ConfigValidator, DefaultContentShaper, RuntimeConfigAssembler
        validator = ConfigValidator()
        shaper = DefaultContentShaper()
        assembler = RuntimeConfigAssembler()

        session = SessionService(files=files_adapter, validator=validator, assembler=assembler)
        renderer = AssemblyService(files=files_adapter, shaper=shaper)
        io = IOService(io_bridge=io_adapter)

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

class BasePathTokens:
    PUD = "<PUD>"
    SHARED = "<SHARED>"

class CfgFragments:
    PUD_CFG = "/.clanker/config.yaml"
    SYSTEM_CFG = "/.clanker/shared-assets/config-fragments/system_cfg.yaml"
    SHARED_CFG = "/.clanker/shared-assets/config-fragments/shared_cfg.yaml"
    TEMPLATE_CFG = "/.clanker/templates/config.template"
    
class DocPaths:
    SHARED_TEMPLATES = "/.clanker/templates/documentation"
    PUD_DOCS = "/.clanker/progress-documentation"
    TEMPL_EXT = ".template"
    DOC_EXT = ".cdoc"

class Layout:
    UI = "/.clanker/shared-assets/layouts/ui.layout"
    PROMPT = "/.clanker/shared-assets/layouts/prompt.layout"
    BTN_ACTIVE = "/.clanker/shared-assets/layouts/btn_active.layout"
    BTN_HL = "/.clanker/shared-assets/layouts/btn_hl.layout"
    BTN_INACTIVE = "/.clanker/shared-assets/layouts/btn_inactive.layout"

class IOControl:
    ACCEPTED = "accepted"
    DECLINED = "declined"
    INVALID = "invalid"
    ABORT_KEYS = ("\x1b", "\x03")
    ACCEPT_KEY = "\x04"
    BACKSPACE_KEYS = ("\x7f", "\x08")

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
class UserTask(Failure): pass

class UserDecline(ControlNotice): pass
class ProgramExit(ControlNotice):
    def get_compliance_msg(self):
        return "Program exited"
class NoConfig(ControlNotice): pass

class ConfigViolations(UserNotice): pass

""" 4. App Abstractions (Models & Engine) """

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
            self.runtime_config = self.session.get_runtime_config()
            self.kb = self.runtime_config.keyboard
            self._wire_num_row()
            self._set_selected_num_btn(None)
            return ActionResult("Bootstrap completed successfully")
        except NoConfig:
            try:
                self.io.get_confirmation("Directory not initialized as clank repo - clankerize?", "yes")
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
            btn.action = self._set_selected_num_btn

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

""" 5. Services """

class SessionService:
    def __init__(
        self,
        files: FileBridgePort,
        validator: ConfigValidatorProtocol,
        assembler: RuntimeConfigAssemblerProtocol
    ) -> None:
        self.files = files
        self.validator = validator
        self.assembler = assembler

    def _get_validated_cfg_fragment(self, fragment_token_path: str) -> dict:
        try:
            raw_content = self.files.get_file_contents(fragment_token_path)
            self.validator.assert_no_quotes(raw_content, fragment_token_path)
            cfg_dict = self.validator.get_as_dict(raw_content)
            self.validator.assert_filesets_not_neglected(cfg_dict, fragment_token_path)
            return cfg_dict
        except ConfigViolations as ex:
            raise UserTask(str(ex)) from ex

    def get_runtime_config(self) -> RuntimeConfig:
        try:
            config_data = self._get_validated_cfg_fragment(BasePathTokens.PUD + CfgFragments.PUD_CFG)
        except FileNotFoundError:
            raise NoConfig

        try:
            kb_def_data = self._get_validated_cfg_fragment(BasePathTokens.SHARED + CfgFragments.SYSTEM_CFG)
            shared_domains_data = self._get_validated_cfg_fragment(BasePathTokens.SHARED + CfgFragments.SHARED_CFG)
        except FileNotFoundError as ex:
            raise ConfigAssemblyFailure(f"Missing configuration fragment: {ex}") from ex

        return self.assembler.assemble(config_data, kb_def_data, shared_domains_data)

    def initialize_workspace(self) -> None:
        if self.files.is_cwd_script_dir():
            raise CorruptClanker("Clanker repository initialized is beyond scope of app.")

        try:
            default_config_data = self._get_validated_cfg_fragment(BasePathTokens.SHARED + CfgFragments.TEMPLATE_CFG)
        except FileNotFoundError as ex:
            raise ConfigAssemblyFailure(f"Missing configuration template: {ex}") from ex

        self.files.write_yaml(BasePathTokens.PUD + Config.DEFAULT_REL_PATH, default_config_data)

        self.files.write_default_documents(
            doc_templ_dir=DocPaths.SHARED_TEMPLATES,
            pud_doc_dir=DocPaths.PUD_DOCS,
            templ_ext=DocPaths.TEMPL_EXT,
            doc_ext=DocPaths.DOC_EXT
        )

class AssemblyService:
    def __init__(self, files: FileBridgePort, shaper: ContentShaper) -> None:
        self.files = files
        self.shaper = shaper

    def hydrate(self, template: str, replacements: dict[str, str]) -> str:
        return self.shaper.hydrate(SystemKeys.DELIM, template, replacements)

    def get_template(self, render: Render) -> str:
        try:
            match render.template:
                case "prompt_template":
                    return self.files.read_asset(BasePathTokens.SHARED + Layout.PROMPT)
                case "ui_template":
                    return self.files.read_asset(BasePathTokens.SHARED + Layout.UI)
        except FileNotFoundError as ex:
            raise CorruptClanker(f"Error loading template for '{render.template}': {ex}") from ex

    def get_repl_map(self, cfg: RuntimeConfig, render: Render) -> dict[str, str]:
        active_resolvers: list[Resolver] = []
        if render.inherit_base:
            active_resolvers.extend(cfg.base_resolvers)
        if render.inherit_domain:
            active_btn = cfg.keyboard.button_map.get(cfg.keyboard.selected_key)
            if active_btn and isinstance(active_btn.inhabitant, Domain):
                active_resolvers.extend(active_btn.inhabitant.resolvers)
        active_resolvers.extend(render.resolvers)
        replacements: dict[str, str] = {}
        for resolver in active_resolvers:
            for key, val in self._resolve(resolver, cfg.keyboard):
                replacements[key] = val
        return replacements

    def _build_manifest_block(self, tag: str, basepath_token: str, fileset_spec: Any) -> str:
        if isinstance(fileset_spec, dict):
            includes = fileset_spec.get("includes", [])
            excludes = fileset_spec.get("excludes", [])
            paths = sorted(
                self.files.get_files(basepath_token, includes, missing_ok=False) -
                self.files.get_files(basepath_token, excludes, missing_ok=True)
            )
        else:
            roots = [fileset_spec] if isinstance(fileset_spec, str) else (fileset_spec or [])
            paths = sorted(self.files.get_files(basepath_token, roots, missing_ok=False))

        lines = []
        for p in paths:
            try:
                content = self.files.read_asset(f"{basepath_token}/{p}")
                line_count = len(content.splitlines())
                lines.append(f"{p} : {line_count} lines")
            except UnicodeDecodeError:
                pass

        return f"<{tag}>\n" + "\n".join(lines) + "\n</" + tag + ">"

    def _resolve(self, resolver: Resolver, keyboard: Keyboard) -> list[tuple[str, str]]:

        if resolver.type == Resolver.Type.MULTI_DOC:
            raw_files = resolver.payload.get("files") or []
            file_specs = [self.shaper.normalize_file_spec(item) for item in raw_files]
            filenames = [spec[0] for spec in file_specs]

            contents_map = self.files.get_contents_with_pud_fallback(filenames)

            fragments = []
            for filename, tail_lines in file_specs:
                basename = Path(filename).name
                raw_content = contents_map.get(filename)

                if raw_content is not None:
                    content = self.shaper.trim_to_tail(raw_content, tail_lines)
                else:
                    content = f"[{resolver.id}: No content found at '{filename}']"

                fragments.append(f"<{basename}>\n{content}\n</{basename}>")

            return [(resolver.id, "\n\n".join(fragments))]

        if resolver.type == Resolver.Type.FULL_PATH_FILE:
            fragments = []

            for item in resolver.payload.get("files", []):
                filename, tail_lines = self.shaper.normalize_file_spec(item)
                tokenized_path = f"{BasePathTokens.PUD}/{filename}"
                try:
                    content = self.files.read_asset(tokenized_path)
                    content = self.shaper.trim_to_tail(content, tail_lines)
                except FileNotFoundError:
                    content = f"[{resolver.id}: No content found at '{filename}']"

                fragments.append(f"<{filename}>\n{content}\n</{filename}>")

            return [(resolver.id, "\n\n".join(fragments))]

        if resolver.type == Resolver.Type.REPO_CONTENT:
            paths = sorted(
                self.files.get_files(BasePathTokens.PUD, resolver.payload.get("includes", []), missing_ok=False) - 
                self.files.get_files(BasePathTokens.PUD, resolver.payload.get("excludes", []), missing_ok=True)
            )

            tree_header = f"<tree>\n" + "\n".join(f"├── {p}" for p in paths) + "\n</tree>"
            
            file_blocks = []
            for p in paths:
                try:
                    content = self.files.read_asset(f"{BasePathTokens.PUD}/{p}").rstrip()  
                    file_blocks.append(f"<{p}>\n{content}\n</{p}>")
                except UnicodeDecodeError:
                    pass

            inner_content = tree_header + "\n" + "\n".join(file_blocks)
            return [(resolver.id, f"<repo-content>\n{inner_content}\n</repo-content>")]

        if resolver.type == Resolver.Type.REPO_MANIFEST:
            manifest_blocks = [
                self._build_manifest_block("pud-manifest", BasePathTokens.PUD, resolver.payload.get("pud_fileset"))
            ]

            if "shared_fileset" in resolver.payload:
                manifest_blocks.append(
                    self._build_manifest_block("shared-manifest", BasePathTokens.SHARED, resolver.payload.get("shared_fileset"))
                )

            return [(resolver.id, "\n".join(manifest_blocks))]

        if resolver.type == Resolver.Type.KB_INFO:
            btn_hl = self.files.read_asset(BasePathTokens.SHARED + Layout.BTN_HL)
            btn_active = self.files.read_asset(BasePathTokens.SHARED + Layout.BTN_ACTIVE)
            btn_inactive = self.files.read_asset(BasePathTokens.SHARED + Layout.BTN_INACTIVE)

            repl_map = {}
            for btn in keyboard.get_unique_buttons():
                label = ""
                template = btn_inactive
                if btn.type == "domain_row":
                    if btn.key == keyboard.selected_key:
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
        self.io_bridge.write(f"{ui_string}\n")

    def to_clipboard(self, text_content: str) -> int:
        return self.io_bridge.to_clipboard(text_content)

    def get_key(self) -> str:
        ch = self.io_bridge.read_char()
        if ch in IOControl.ABORT_KEYS:
            raise ProgramExit
        return ch.lower()

    def get_confirmation(self, prompt_msg: str, required_phrase: str | None = None) -> None:
        instructions = f"Type '{required_phrase}' and press [Ctrl+D] to confirm, or [ESC/Ctrl+C] to cancel.\n> "
        if required_phrase is None:
            instructions = "Press [Ctrl+D] to confirm, or [ESC/Ctrl+C] to cancel.\n"            
        base_msg = f"\n{prompt_msg}\n{instructions}"
        self.io_bridge.write(base_msg)
        while True:
            status, value = self.io_bridge.get_acceptance(required_phrase)
            if status == IOControl.ACCEPTED:
                return
            if status == IOControl.DECLINED:
                raise UserDecline
            if status == IOControl.INVALID:
                err = f"Invalid confirmation. Expected '{required_phrase}', got '{value}'. Try again.\n"
                self.io_bridge.write(base_msg + err + "> ")

""" 6. Bridge Ports"""

class IOBridgePort(Bridge):
    @abstractmethod
    def to_clipboard(self, text_content: str) -> int: pass
    @abstractmethod
    def write(self, text: str) -> None: pass
    @abstractmethod
    def read_char(self) -> str: pass
    @abstractmethod
    def get_acceptance(self, required_phrase: str | None) -> tuple[str, str]: pass

class ContentShaper(Protocol):
    def normalize_file_spec(self, item: str | dict) -> tuple[str, int | None]: ...
    def trim_to_tail(self, content: str, tail_lines: int | None) -> str: ...
    def hydrate(self, delim: str, template: str, replacements: dict[str, str]) -> str: ...

class ConfigValidatorProtocol(Protocol):
    def assert_no_quotes(self, raw_text: str, filepath: str = "") -> None: ...
    def get_as_dict(self, raw_text: str) -> dict: ...
    def assert_filesets_not_neglected(self, cfg_frag: dict, filepath: str = "") -> None: ...

class RuntimeConfigAssemblerProtocol(Protocol):
    def assemble(self, config_data: dict, kb_def_data: dict, shared_domains_data: dict) -> RuntimeConfig: ...

class FileBridgePort(Bridge):

    @abstractmethod
    def get_file_contents(self, tokenized_path: str) -> str: pass

    @abstractmethod
    def write_default_documents(
        self, doc_templ_dir: str, pud_doc_dir: str, templ_ext: str, doc_ext: str
    ) -> None: pass

    @abstractmethod
    def is_cwd_script_dir(self) -> bool: pass

    @abstractmethod
    def write_yaml(self, tokenized_path: str, data: dict) -> None: pass

    @abstractmethod
    def read_asset(self, tokenized_path: str | Path) -> str: pass

    @abstractmethod
    def get_files(
        self,
        basepath_token: str,
        rel_roots: list[str | Path],
        missing_ok: bool = False
    ) -> set[Path]: pass

    @abstractmethod
    def get_contents_with_pud_fallback(self, file_names: list[str]) -> dict[str, str | None]: pass

""" 7. Script Entrypoint """

if __name__ == "__main__":
    main()