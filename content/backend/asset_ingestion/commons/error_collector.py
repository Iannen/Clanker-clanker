from dataclasses import dataclass, field
from backend.core import engine_deps as d


@dataclass
class ErrorCollector(d.Report):
    soft_complaints: list[d.Soft] = field(default_factory=list)
    critical_complaints: list[d.Critical] = field(default_factory=list)

    def get_all_complaints(self) -> list[d.Soft]:
        return self.soft_complaints + self.critical_complaints

    def get_critical_complaints(self) -> list[str]:
        return ["crit\n" for c in self.critical_complaints]

    def has_crits(self) -> bool:
        return len(self.critical_complaints) > 0

    def accept(self, compl: d.Complaint) -> None:
        match compl:
            case d.Critical(): self.critical_complaints.append(compl)
            case d.Soft(): self.soft_complaints.append(compl)