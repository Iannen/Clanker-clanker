from core.engine_deps import Report, Complaint, Critical, Soft



class ErrorCollector(Report):
    def __init__(self) -> None:
        self._soft_complaints: list[Soft] = []
        self._critical_complaints: list[Critical] = []

    def get_complaints(self) -> list[str]:
        return ["soft\n" for c in self._soft_complaints]

    def get_all_complaints(self) -> list[Soft]:
        return self._soft_complaints+self._critical_complaints

    def get_critical_complaints(self) -> list[str]:
        return ["crit\n" for c in self._critical_complaints]

    def has_crits(self) -> bool:
        return len(self._critical_complaints) > 0

    def accept(self, compl: Complaint) -> None:
        match compl:
            case Critical(): self._critical_complaints.append(compl)
            case Soft(): self._soft_complaints.append(compl)
