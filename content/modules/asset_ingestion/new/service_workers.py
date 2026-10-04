from stdlib import StrEnum, dataclass
from core import RepoItem, CorruptClanker, Config, Render, AssetPack, Keyboard
from ...asset_ingestion import ConfigExtractor, FilelistParser, FilesetParser, FilelistValidator, FilesetValidator, CollisionDetector, Missing, Malformed, ErrorCollector, DomParser, ResolverParser, UIRenderParser, KeyboardParser, OverflowHandler

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
        extractor = ConfigExtractor(self.collector, (self.clank_cfg, self.pud_cfg))
        clank_fl, pud_fl = extractor.get_maps(FilelistParser)
        clank_fs, pud_fs = extractor.get_maps(FilesetParser)
        unified_fl = clank_fl | pud_fl if clank_fl and pud_fl else None
        unified_fs = clank_fs | pud_fs if clank_fs and pud_fs else None
        clank_br, pud_br = extractor.get_singles(ResolverParser, (clank_fs, clank_fl), (unified_fs, unified_fl))
        clank_doms, pud_doms = extractor.get_maps(DomParser, (clank_fs, clank_fl), (unified_fs, unified_fl))

        sys_ext = ConfigExtractor(self.collector, (self.sys_cfg,))
        ui_render, = sys_ext.get_singles(UIRenderParser,(clank_fs, clank_fl))
        kb, = sys_ext.get_singles(KeyboardParser)

        populated_kb = OverflowHandler(self.collector).do_it(clank_br, pud_br, clank_doms, pud_doms, kb)

        list_validator = FilelistValidator(self.collector).validate_clank(clank_doms, self.clank_doc_assets, self.clank_cfg)
        list_validator.validate_pud(pud_doms, self.pud_doc_assets, self.pud_cfg)        
        fileset_validator = FilesetValidator(self.collector).validate_clank(clank_doms, self.clank_doc_assets, self.clank_cfg)
        fileset_validator.validate_pud(pud_doms, self.pud_doc_assets, self.pud_cfg)      

        CollisionDetector(self.collector).detect(self.clank_doc_assets) 
        CollisionDetector(self.collector).detect(self.pud_doc_assets)
        
        return ui_render, populated_kb 
