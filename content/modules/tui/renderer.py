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
    """ this class turns a report into a str"""
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
    """ this class should encapsulate all the business of turning a kb/ui render into a str i think we can give it the filesadapter so it can get its templates."""
    DELIM = "§"
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
    """ this class delegates to the above two classes , and uses the terminalport."""
    io_bridge: TerminalPort
    files: DiskPort
    shaper: TUIContentShaper = field(default_factory=TUIContentShaper)
    PROCEED_QUESTION = "Proceed anyway?" # is this required here? wtf

    def post_question(self, result: StartResult | ClankerizeResult, affirmative_cmd: type, declined_cmd: type) -> Command:
        match result:
            case StartResult():
                accepted = True
                if result.report.get_all_complaints():
                    question = self.start_confirmation(result.report)
                    accepted = self.io_bridge.get_acceptance(question)
            case ClankerizeResult():
                question = self.clankerize_confirmation(result.report)
                accepted = self.io_bridge.get_acceptance(question)
            case _:
                accepted = False
        return affirmative_cmd() if accepted else declined_cmd()

    def get_acknowledgement(self, result: TerminateResult, exit_cmd: type) -> Command:
        question = self.termination_acknowledgment(result.report)
        self.io_bridge.get_acceptance(question)
        return exit_cmd()

    def display_result(self, result: KbCmdResult | ExitResult) -> None:
        if isinstance(result, KbCmdResult):
            self.render_result(result)

    def render_result(self, command_result: KbCmdResult) -> None:
        try:
            template = self.files.read_asset(ClankerAssets.layouts.UI)
        except NoSuchFile as ex:
            raise CorruptClanker(f"Error loading template for '{command_result.ui_render.template}': {ex}") from ex
        repl_map = self._res_ui(command_result.kb)
        repl_map["msg"] = self.shaper.shape_command_result(command_result)
        ui_string = self.shaper.hydrate(template, repl_map)
        self.io_bridge.write(f"{ui_string}\n")

    def _res_ui(self, kb: Keyboard) -> dict[str, str]:
        btn_hl = self.files.read_asset(ClankerAssets.layouts.BTN_HL)
        btn_active = self.files.read_asset(ClankerAssets.layouts.BTN_ACTIVE)
        btn_inactive = self.files.read_asset(ClankerAssets.layouts.BTN_INACTIVE)

        repl_map = {}
        for btn in kb.get_btns(DomButton):
            template = btn_inactive
            label = btn.inhabitant.name if btn.inhabitant else ""
            if btn == kb.selected_dom_btn: template = btn_hl
            elif btn.inhabitant: template = btn_active
            repl_map |= self.shaper.shape_button_replacements(btn, label, template)
        for btn in kb.get_btns(PromptButton):
            label = btn.inhabitant.name if btn.inhabitant else ""
            template = btn_active if btn.inhabitant else btn_inactive   
            repl_map |= self.shaper.shape_button_replacements(btn, label, template)
            
        return repl_map

    @classmethod
    def termination_acknowledgment(cls, report: Report) -> Question:
        msg = ComplaintsFormatter.format(report)
        return Question(
            message=msg,
            required_phrase=None,
            instructions="Press any key to exit.\n> "
        )

    @classmethod
    def start_confirmation(cls, report: Report) -> Question:
        report_str = ComplaintsFormatter.format(report)
        prompt_msg = f"{report_str}\n{cls.PROCEED_QUESTION}" if report_str else cls.PROCEED_QUESTION
        return Question(
            message=prompt_msg,
            required_phrase=None,
            instructions="Press [Ctrl+D] to proceed, or [ESC/Ctrl+C] to decline.\n> "
        )

    @classmethod
    def clankerize_confirmation(cls, report: Report) -> Question:
        parts = []
        report_str = ComplaintsFormatter.format(report)
        if report_str:
            parts.append(report_str)
        parts.append(QuestionPhrases.INIT_REPO)
        prompt_msg = "\n".join(parts)
        return Question(
            message=prompt_msg,
            required_phrase=QuestionPhrases.REQUIRED_PHRASE,
            instructions=QuestionPhrases.CONFIRMATION_INSTRUCTIONS.format(required_phrase=QuestionPhrases.REQUIRED_PHRASE),
            error_template=QuestionPhrases.CONFIRMATION_INVALID_ERR
        )

""" 
below classes hold str values for use other places 
we can reference them in the test system when we do asserts.
these are aux classes, so to speak.
"""

class ActionResult:
    """ this class is used by test system to evaluate rendered ui's """
    BOOTSTRAP_SUCCESS = "Bootstrap completed successfully"
    UNBOUND_KEY = "No action bound to key '{key}'"
    DOMAIN_SELECTED = "Domain '{domain}' on key '{key}' selected"
    KEY_EMPTY = "Key '{key}' is empty"
    COPIED_TO_CLIPBOARD = "Copied {lines} lines ({chars} chars) to clipboard"

    MSG_DEFAULT: str = "Program exited"
    MSG_DECLINED_INIT: str = "User declined to clankerize project"
    MSG_DECLINED_BOOTSTRAP: str = "Bootstrap declined by user"

class QuestionPhrases:
    REQUIRED_PHRASE = "yes"
    INIT_REPO = "Directory not initialized as clank repo - clankerize?"
    CONFIRMATION_INSTRUCTIONS = "Type '{required_phrase}' and press [Ctrl+D] to confirm, or [ESC/Ctrl+C] to cancel.\n> "
    CONFIRMATION_INVALID_ERR = "Invalid confirmation. Expected '{required_phrase}', got '{value}'. Try again.\n"