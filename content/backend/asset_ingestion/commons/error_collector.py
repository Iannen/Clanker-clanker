from backend.core import engine_deps as d


class ErrorCollector(d.Report):
    def __init__(self) -> None:
        self._soft_complaints: list[d.Soft] = []
        self._critical_complaints: list[d.Critical] = []

    def get_all_complaints(self) -> list[d.Soft]:
        return self._soft_complaints+self._critical_complaints

    def get_critical_complaints(self) -> list[str]:
        return ["crit\n" for c in self._critical_complaints]

    def has_crits(self) -> bool:
        return len(self._critical_complaints) > 0

    def accept(self, compl: d.Complaint) -> None:
        match compl:
            case d.Critical(): self._critical_complaints.append(compl)
            case d.Soft(): self._soft_complaints.append(compl)