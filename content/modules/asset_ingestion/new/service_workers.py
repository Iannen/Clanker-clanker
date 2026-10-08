from stdlib import StrEnum, dataclass
from core import RepoItem, CorruptClanker, Config, Render, AssetPack, Keyboard, Filelist, Fileset, UIRender, SharedBaseResolver, PudBaseResolver, SharedDomain, PudDomain
from ...asset_ingestion import Missing, Malformed, ErrorCollector, OverflowHandler2, FilelistValidator2, FilesetValidator2, CollisionDetector
from ...asset_ingestion import Numap, NuConfigExtractor

class ClassificationResult(StrEnum):
    ALL_PRESENT = "all"
    NONE_PRESENT = "none"
    MIXED = "mix"

class ItemClassifier:
    def __init__(self, ec: ErrorCollector):
        self.ec = ec
        self.present, self.missing, self.malformed = [], [], []

    def classify(self, item):
        if isinstance(item, RepoItem): self.present.append(item); return item 
        if isinstance(item, Missing):  self.missing.append(item); return None
        if isinstance(item, Malformed): self.malformed.append(item); return None
        raise TypeError(f"ItemClassifier cannot classify object of type {type(item).__name__}: {item!r}")

    def evaluate(self) -> ClassificationResult:
        has_present = bool(self.present)
        has_invalid = bool(self.missing or self.malformed)

        if not has_present and not has_invalid: raise CorruptClanker(f"{type(self).__name__} was supplied no items to classify")
        if has_present and has_invalid: return ClassificationResult.MIXED
        if has_present: return ClassificationResult.ALL_PRESENT
        return ClassificationResult.NONE_PRESENT

    def complain(self):
        for c in self.missing + self.malformed:  self.ec.accept(c)

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

        numap = Numap(self.collector)
        clank_ext = NuConfigExtractor(numap, self.collector, self.clank_cfg)
        clank_ext.extract_from_map(Filelist)
        clank_ext.extract_from_map(Fileset)
        clank_ext.extract_from_map(SharedDomain)
        clank_ext.extract_single(SharedBaseResolver)

        pud_ext = NuConfigExtractor(numap, self.collector, self.pud_cfg)
        pud_ext.extract_from_map(Filelist)
        pud_ext.extract_from_map(Fileset)
        pud_ext.extract_from_map(PudDomain)
        pud_ext.extract_single(PudBaseResolver)

        system_extractor = NuConfigExtractor(numap, self.collector, self.sys_cfg)
        system_extractor.extract_single(UIRender)
        system_extractor.extract_single(Keyboard)

        ui_render, populated_kb = OverflowHandler2(self.collector).do_it(numap)

        list_validator = FilelistValidator2(
            self.collector,
            self.clank_doc_assets,
            self.clank_cfg,
            self.pud_doc_assets,
            self.pud_cfg,
            numap
        )
        list_validator.validate_clank()
        list_validator.validate_pud()        

        fileset_validator = FilesetValidator2(self.collector)
        fileset_validator.validate_pud(numap, self.pud_doc_assets, self.pud_cfg)      
        fileset_validator.validate_clank(numap, self.clank_doc_assets, self.clank_cfg)

        CollisionDetector(self.collector).detect(self.clank_doc_assets) 
        CollisionDetector(self.collector).detect(self.pud_doc_assets)
        return ui_render, populated_kb 
