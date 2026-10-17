from stdlib import dataclass, field, re
from core import ClankerAssets, DomButton, PromptButton, Keyboard, CorruptClanker, NewBtn
from core.engine_deps import (
    TerminalPort, StartResult, ClankerizeResult, TerminateResult,
    Report, MissingEntityFields, UnsatisfiedFiles, Missing, Malformed, 
    UnsatisfiedFilesetSubjects, FilenameCollision, DomainOverflow, Complaint, Question, 
    BootstrapSuccess, UnboundKeyResult, DomainSelectedResult, UninhabitedDomainResult, 
    UninhabitedPromptResult, PromptRenderResult, KbCmdResult, NoSuchFile, DiskPort, ExitResult, Command
)

class ComplaintsFormatter:
    """This class turns a report into a str"""
    @classmethod
    def format(cls, report: Report) -> str:
        parts = []
        crits = report.get_critical_complaints()
        if crits:
            parts.append("Critical errors:\n" + "\n".join(crits))
        softs = report.get_all_complaints()
        if softs:
            formatted_softs = [cls._format_complaint(c) for c in softs]
            parts.append("Soft complaints:\n" + "\n".join(formatted_softs))
        return "\n".join(parts)

    @classmethod
    def _format_complaint(cls, complaint: Complaint) -> str:
        match complaint:
            case Malformed():
                return f"{complaint.__class__.__name__}: '{complaint.name}' at '{complaint.path}': \n{complaint.details}"
            case Missing():
                return f"{complaint.__class__.__name__}: '{complaint.name}' not found at '{complaint.paths}'"
            case FilenameCollision():
                formatted_paths = ", ".join(f"'{p}'" for p in sorted(complaint.paths))
                return (
                    f"Filename collision detected for '{complaint.filename}'. Coexisting paths: {formatted_paths}\n"
                    f"\tDefaulted to using: '{complaint.chosen_path}'"
                )
            case DomainOverflow():
                row_keys = [btn.key for btn in complaint.buttons if hasattr(btn, "key")]
                accepted_count = sum(len(btn.domains) for btn in complaint.buttons if hasattr(btn, "domains"))
                received_count = accepted_count + len(complaint.discarded_domains)
                msg = f"Domain overflow in row '{row_keys}': received {received_count} domains, but only {accepted_count} slots are available."
                for dom in complaint.discarded_domains:
                    msg += f"\n\tDomain '{dom.name}' was discarded."
                return msg
            case UnsatisfiedFiles():
                files_str = "\n\t- ".join(f"'{f.name}'" for f in complaint.files)
                return (
                    f"Removed {len(complaint.files)} file reference(s) "
                    f"unsatisfied by asset packs:\n\t- {files_str}"
                )
            case UnsatisfiedFilesetSubjects():
                subjects_str = "\n\t- ".join(f"'{s}'" for s in complaint.subjects)
                return (
                    f"Asset pack '{complaint.assetpack.token}': Removed {len(complaint.subjects)} unsatisfied subject(s):\n\t- {subjects_str}"
                )
            case MissingEntityFields():
                fields_str = ", ".join(f"'{f.name}'" for f in complaint.missing_fields)
                return (
                    f"Failed to instantiate '{complaint.entity_cls.__name__}' due to missing required field(s): {fields_str}\n"
                    f"\tReceived data: {complaint.data}"
                )
            case _:
                return str(complaint)

class TUIContentShaper:
    """This class encapsulates all the business of turning a kb/ui render into a str"""
    DELIM = "§"

    def render_view(self, command_result: KbCmdResult, files: DiskPort) -> str:
        try:
            template = files.read_asset(ClankerAssets.layouts.UI)
        except NoSuchFile as ex:
            raise CorruptClanker(f"Error loading template for '{command_result.ui_render.template}': {ex}") from ex
        repl_map = self._res_ui(command_result.kb, files)
        repl_map["msg"] = self.shape_command_result(command_result)
        return self.hydrate(template, repl_map)

    def _res_ui(self, kb: Keyboard, files: DiskPort) -> dict[str, str]:
        btn_hl = files.read_asset(ClankerAssets.layouts.BTN_HL)
        btn_active = files.read_asset(ClankerAssets.layouts.BTN_ACTIVE)
        btn_inactive = files.read_asset(ClankerAssets.layouts.BTN_INACTIVE)

        repl_map = {}
        for btn in kb.get_btns(DomButton):
            template = btn_inactive
            label = btn.inhabitant.name if btn.inhabitant else ""
            if btn == kb.selected_dom_btn: template = btn_hl
            elif btn.inhabitant: template = btn_active
            repl_map |= self.shape_button_replacements(btn, label, template)
        for btn in kb.get_btns(PromptButton):
            label = btn.inhabitant.name if btn.inhabitant else ""
            template = btn_active if btn.inhabitant else btn_inactive   
            repl_map |= self.shape_button_replacements(btn, label, template)
            
        return repl_map

    def shape_button_replacements(self, btn: NewBtn, label: str, template: str) -> dict[str, str]:
        lines = template.strip("\n").splitlines()
        norm_label = label[:6].ljust(6)
        mapped_lines = [
            lines[0],
            lines[1],
            lines[2].replace(self.DELIM, btn.key, 1),
            lines[3],
            lines[4].replace(self.DELIM * 6, norm_label, 1),
        ]
        return {f"{btn.key}{idx}": line for idx, line in enumerate(mapped_lines)}

    def shape_action_result(self, msg: str, width: int = 117) -> str:
        return f"{msg:<{width}}"[:width]

    def hydrate(self, template: str, replacements: dict[str, str]) -> str:
        pattern = re.compile(rf"{self.DELIM}([^{self.DELIM}]+){self.DELIM}")
        return pattern.sub(
            lambda m: replacements.get(m.group(1).strip(), m.group(0)),
            template
        )

    def shape_command_result(self, command_result: KbCmdResult, width: int = 117) -> str:
        match command_result:
            case BootstrapSuccess():
                msg = ActionResult.BOOTSTRAP_SUCCESS
            case UnboundKeyResult():
                msg = ActionResult.UNBOUND_KEY.format(key=command_result.cmd.char)
            case DomainSelectedResult():
                msg = ActionResult.DOMAIN_SELECTED.format(domain=command_result.btn.inhabitant.name, key=command_result.btn.key)
            case UninhabitedDomainResult():
                msg = ActionResult.KEY_EMPTY
            case UninhabitedPromptResult():
                msg = ActionResult.UNBOUND_KEY.format(key=command_result.btn.key)
            case PromptRenderResult():
                msg = ActionResult.COPIED_TO_CLIPBOARD.format(lines=command_result.lines, chars=command_result.chars)
            case _:
                msg = ""
        return self.shape_action_result(msg, width)


@dataclass
class TUIRenderer:
    """This class delegates to helper classes and uses the terminal port."""
    io_bridge: TerminalPort
    files: DiskPort
    shaper: TUIContentShaper = field(default_factory=TUIContentShaper)

    def post_question(self, result: StartResult | ClankerizeResult, affirmative_cmd: type, declined_cmd: type) -> Command:
        match result:
            case StartResult():
                if not result.report.get_all_complaints():
                    return affirmative_cmd()
                report_str = ComplaintsFormatter.format(result.report)
                prompt_msg = f"{report_str}\n{QuestionPhrases.PROCEED_QUESTION}"
                question = Question(
                    message=prompt_msg,
                    required_phrase=None,
                    instructions="Press [Ctrl+D] to proceed, or [ESC/Ctrl+C] to decline.\n> "
                )
            case ClankerizeResult():
                parts = []
                report_str = ComplaintsFormatter.format(result.report)
                if report_str:
                    parts.append(report_str)
                parts.append(QuestionPhrases.INIT_REPO)
                prompt_msg = "\n".join(parts)
                question = Question(
                    message=prompt_msg,
                    required_phrase=QuestionPhrases.REQUIRED_PHRASE,
                    instructions=QuestionPhrases.CONFIRMATION_INSTRUCTIONS.format(required_phrase=QuestionPhrases.REQUIRED_PHRASE),
                    error_template=QuestionPhrases.CONFIRMATION_INVALID_ERR
                )
            case _: raise Exception(f"some appropriate ex to say {result} should not go here") 

        accepted = self.io_bridge.get_acceptance(question)
        return affirmative_cmd() if accepted else declined_cmd()

    def get_acknowledgement(self, result: TerminateResult, exit_cmd: type) -> Command:
        msg = ComplaintsFormatter.format(result.report)
        question = Question(
            message=msg,
            required_phrase=None,
            instructions="Press any key to exit.\n> "
        )
        self.io_bridge.get_acceptance(question)
        return exit_cmd()

    def display_result(self, result: KbCmdResult | ExitResult) -> None:
        if isinstance(result, KbCmdResult):
            ui_string = self.shaper.render_view(result, self.files)
            self.io_bridge.write(f"{ui_string}\n")


class ActionResult:
    """Used by test system to evaluate rendered UIs"""
    BOOTSTRAP_SUCCESS = "Bootstrap completed successfully"
    UNBOUND_KEY = "No action bound to key '{key}'"
    DOMAIN_SELECTED = "Domain '{domain}' on key '{key}' selected"
    KEY_EMPTY = "Key '{key}' is empty"
    COPIED_TO_CLIPBOARD = "Copied {lines} lines ({chars} chars) to clipboard"

    MSG_DEFAULT: str = "Program exited"
    MSG_DECLINED_INIT: str = "User declined to clankerize project"
    MSG_DECLINED_BOOTSTRAP: str = "Bootstrap declined by user"


class QuestionPhrases:
    """Holds question phrases and instructions"""
    REQUIRED_PHRASE = "yes"
    INIT_REPO = "Directory not initialized as clank repo - clankerize?"
    PROCEED_QUESTION = "Proceed anyway?"
    CONFIRMATION_INSTRUCTIONS = "Type '{required_phrase}' and press [Ctrl+D] to confirm, or [ESC/Ctrl+C] to cancel.\n> "
    CONFIRMATION_INVALID_ERR = "Invalid confirmation. Expected '{required_phrase}', got '{value}'. Try again.\n"