from core.engine_deps import Report, MissingEntityFields, UnsatisfiedFiles, Missing, Malformed, UnsatisfiedFilesetSubjects, FilenameCollision, DomainOverflow, Complaint

class TUIQuestions:
    PROCEED_QUESTION = "Proceed anyway?"

    @classmethod
    def complaints_proceed(cls, complaints: list[str]) -> str:
        complaints_str = "\n".join(complaints)
        return f"{complaints_str}\n{cls.PROCEED_QUESTION}"

    @classmethod
    def start_confirmation(cls, report: Report) -> str:
        softs = report.get_all_complaints()
        formatted_softs = [ComplaintsFormatter._format_complaint(c) for c in softs]
        return cls.complaints_proceed(formatted_softs)

    @classmethod
    def clankerize_confirmation(cls, report: Report) -> str:
        softs = report.get_all_complaints()
        parts = []
        if softs:
            formatted_softs = [ComplaintsFormatter._format_complaint(c) for c in softs]
            parts.append("\n".join(formatted_softs))
        parts.append(UserQuestions.INIT_REPO)
        return "\n".join(parts)

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