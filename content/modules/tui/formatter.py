from core.engine_deps import Complaint, UnsatisfiedFiles

class ComplaintsFormatter:
    @classmethod
    def format(cls, complaint: Complaint) -> str:
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