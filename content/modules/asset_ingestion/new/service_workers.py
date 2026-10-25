from stdlib import StrEnum, dataclass
from core import CorruptClanker, Render, Keyboard
from ...asset_ingestion import ErrorCollector, OverflowHandler2, FilelistValidator2, FilesetValidator2
from ...asset_ingestion import Numap, AssetPack, RepoItem, Config
from core.engine_deps import Complaint

class ClassificationResult(StrEnum):
    ALL_PRESENT = "all"
    NONE_PRESENT = "none"
    MIXED = "mix"

class ItemClassifier:
    def __init__(self, ec: ErrorCollector):
        self.ec = ec
        self.present, self.complaints = [], []

    def classify(self, item):
        if isinstance(item, RepoItem): self.present.append(item); return item
        if isinstance(item, Complaint): self.complaints.append(item); return None
        raise TypeError(f"ItemClassifier cannot classify object of type {type(item).__name__}: {item!r}")

    def evaluate(self) -> ClassificationResult:
        has_present = bool(self.present)
        has_invalid = bool(self.complaints)

        if not has_present and not has_invalid: raise CorruptClanker(f"{type(self).__name__} was supplied no items to classify")
        if has_present and has_invalid: return ClassificationResult.MIXED
        if has_present: return ClassificationResult.ALL_PRESENT
        return ClassificationResult.NONE_PRESENT

    def complain(self):
        for c in self.complaints: self.ec.accept(c)

@dataclass
class Assembler:
    collector: ErrorCollector | None
    clank_cfg: Config  | None
    sys_cfg: Config  | None
    clank_doc_assets: AssetPack  | None
    pud_cfg: Config  | None
    pud_doc_assets: AssetPack  | None
    pud_content_assets: AssetPack  | None

    def assemble(self, pud_res: ClassificationResult) ->  tuple[Render, Keyboard]:

        numap = Numap(self.collector, self.clank_cfg, self.pud_cfg, self.sys_cfg)
        numap.extract_all()

        list_validator = FilelistValidator2(
            self.collector,
            self.clank_doc_assets,
            self.pud_doc_assets,
            numap
        )
        list_validator.validate()

        fileset_validator = FilesetValidator2(
            self.collector,
            numap,
            self.clank_doc_assets,
            self.pud_content_assets,
        )
        fileset_validator.validate()
        return OverflowHandler2(self.collector).do_it(numap) #ui_render, populated_kb
