from stdlib import dataclass
from core.engine_deps import (
    TerminalPort, IngestionResult, StartResult, ClankerizeResult, TerminateResult,
    Report, MissingEntityFields, UnsatisfiedFiles, Missing, Malformed, 
    UnsatisfiedFilesetSubjects, FilenameCollision, DomainOverflow, Complaint, Question, 
    BootstrapSuccess, UnboundKeyResult, DomainSelectedResult, UninhabitedDomainResult, 
    UninhabitedPromptResult, PromptRenderResult, KbCmdResult
)

@dataclass
class TUIQuestions:
    io_bridge: TerminalPort
    PROCEED_QUESTION = "Proceed anyway?"

    def dispatch(self, bootstrap_res: IngestionResult) -> bool:
        match bootstrap_res:
            case StartResult():
                if not bootstrap_res.report.get_all_complaints():
                    return True
                question = self.start_confirmation(bootstrap_res.report)
                return self.io_bridge.get_acceptance(question)

            case ClankerizeResult():
                question = self.clankerize_confirmation(bootstrap_res.report)
                return self.io_bridge.get_acceptance(question)

            case TerminateResult():
                question = self.termination_acknowledgment(bootstrap_res.report)
                self.io_bridge.get_acceptance(question)
                return True
            case _:
                return False

    @classmethod
    def termination_acknowledgment(cls, report: Report) -> Question:
        all_crits = report.get_critical_complaints()
        all_softs = report.get_complaints()
        msg = "Critical errors:\n" + "\n".join(all_crits)
        if all_softs:
            msg += "\nSoft complaints:\n" + "\n".join(all_softs)
        return Question(
            message=msg,
            required_phrase=None,
            instructions="Press any key to exit.\n> "
        )

    @classmethod
    def complaints_proceed(cls, complaints: list[str]) -> str:
        complaints_str = "\n".join(complaints)
        return f"{complaints_str}\n{cls.PROCEED_QUESTION}"

    @classmethod
    def start_confirmation(cls, report: Report) -> Question:
        softs = report.get_all_complaints()
        prompt_msg = cls.complaints_proceed([ComplaintsFormatter._format_complaint(c) for c in softs])
        return Question(
            message=prompt_msg,
            required_phrase=None,
            instructions="Press [Ctrl+D] to proceed, or [ESC/Ctrl+C] to decline.\n> "
        )

    @classmethod
    def clankerize_confirmation(cls, report: Report) -> Question:
        softs = report.get_all_complaints()
        parts = []
        if softs:
            formatted_softs = [ComplaintsFormatter._format_complaint(c) for c in softs]
            parts.append("\n".join(formatted_softs))
        parts.append(UserQuestions.INIT_REPO)
        prompt_msg = "\n".join(parts)
        return Question(
            message=prompt_msg,
            required_phrase=UserQuestions.REQUIRED_PHRASE,
            instructions=UserQuestions.CONFIRMATION_INSTRUCTIONS.format(required_phrase=UserQuestions.REQUIRED_PHRASE),
            error_template=UserQuestions.CONFIRMATION_INVALID_ERR
        )

class ComplaintsFormatter:
    @classmethod
    def format(cls, report: Report) -> str:
        softs = report.get_all_complaints()
        return "\n".join(cls._format_complaint(c) for c in softs)

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

class UserQuestions:
    REQUIRED_PHRASE = "yes"
    INIT_REPO = "Directory not initialized as clank repo - clankerize?"
    CONFIRMATION_INSTRUCTIONS = "Type '{required_phrase}' and press [Ctrl+D] to confirm, or [ESC/Ctrl+C] to cancel.\n> "
    CONFIRMATION_INVALID_ERR = "Invalid confirmation. Expected '{required_phrase}', got '{value}'. Try again.\n"

    @classmethod
    def overflow_proceed(cls, dof_report: str) -> str:
        return f"{dof_report}\nDo you wish to proceed with overflowed domains trimmed?"

    @classmethod
    def complaints_proceed(cls, complaints: list[str]) -> str:
        return f"{"\n".join(complaints)}\nProceed anyway?"


from stdlib import re
from core import NewBtn
class SystemKeys:
    DELIM = "§"

class TUIContentShaper:

    def shape_button_replacements(self, btn: NewBtn, label: str, template: str) -> dict[str, str]:
        lines = template.strip("\n").splitlines()
        norm_label = label[:6].ljust(6)
        mapped_lines = [
            lines[0],
            lines[1],
            lines[2].replace(SystemKeys.DELIM, btn.key, 1),
            lines[3],
            lines[4].replace(SystemKeys.DELIM * 6, norm_label, 1),
        ]
        return {f"{btn.key}{idx}": line for idx, line in enumerate(mapped_lines)}

    def shape_action_result(self, msg: str, width: int = 117) -> str:
        return f"{msg:<{width}}"[:width]

    def hydrate(self, template: str, replacements: dict[str, str]) -> str:
        pattern = re.compile(rf"{SystemKeys.DELIM}([^{SystemKeys.DELIM}]+){SystemKeys.DELIM}")
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

    def __init__(self, message: str):
        self.message = message