from core.engine_deps import Complaint, UnsatisfiedFiles, Report
from ..tui import TUIQuestions

class ComplaintsFormatter:
    @classmethod
    def format(cls, report: Report) -> str:
        softs = report.get_all_complaints()
        formatted_softs = [cls._format_complaint(c) for c in softs]
        prompt_msg = TUIQuestions.complaints_proceed(formatted_softs)
        instructions = "Press [Ctrl+D] to proceed, or [ESC/Ctrl+C] to decline.\n> "
        return f"\n{prompt_msg}\n{instructions}"

    @classmethod
    def _format_complaint(cls, complaint: Complaint) -> str:
        match complaint:
            case UnsatisfiedFiles():
                files_str = "\n\t- ".join(f"'{f.name}'" for f in complaint.files)
                return (
                    f"Removed {len(complaint.files)} file reference(s) "
                    f"unsatisfied by asset packs:\n\t- {files_str}"
                )
            case _:
                if hasattr(complaint, "to_string"):
                    return complaint.to_string()
                return str(complaint)