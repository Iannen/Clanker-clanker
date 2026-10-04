from stdlib import StrEnum, dataclass
from core import RepoItem, CorruptClanker, Config, Render, AssetPack, Keyboard
from ...asset_ingestion import ConfigExtractor, FilelistParser, FilesetParser, SysConfigExtractorOld, FilelistValidator, FilesetValidator, CollisionDetector, Missing, Malformed, ErrorCollector, DomParser, ResolverParser, SysConfigExtractor, UIRenderParser, KeyboardParser


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
        extractor = ConfigExtractor(self.collector, self.clank_cfg, self.pud_cfg)
        clank_fl, pud_fl, unified_fl = extractor.get_maps(FilelistParser)
        clank_fs, pud_fs, unified_fs = extractor.get_maps(FilesetParser)
        # must crit if clank dont got br. 
        br_cl, br_pud, br_uni = extractor.get_maps(ResolverParser, (clank_fs, clank_fl), (unified_fs, unified_fl))
        pud_baseres = list(br_cl.values())[0] # use get_one here
        clank_doms, pud_doms, unified_doms = extractor.get_maps(DomParser, (clank_fs, clank_fl, pud_baseres), (unified_fs, unified_fl, pud_baseres))
        
        ui_render, kb = SysConfigExtractorOld(self.collector, self.sys_cfg).get_final_product(clank_doms, pud_doms)       
        sys_ext = SysConfigExtractor(self.collector, self.sys_cfg)

        ui_render2 = sys_ext.get_one(UIRenderParser,(clank_fs, clank_fl))
        kb2 = sys_ext.get_one(KeyboardParser)
        finished_kb = self._validate_assemble(br_cl, br_pud, unified_doms, kb2)

        list_validator = FilelistValidator(self.collector).validate_clank(clank_doms, self.clank_doc_assets, self.clank_cfg)
        list_validator.validate_pud(pud_doms, self.pud_doc_assets, self.pud_cfg) 
        
        fileset_validator = FilesetValidator(self.collector).validate_clank(clank_doms, self.clank_doc_assets, self.clank_cfg)
        fileset_validator.validate_pud(pud_doms, self.pud_doc_assets, self.pud_cfg)      

        CollisionDetector(self.collector).detect(self.clank_doc_assets) 
        CollisionDetector(self.collector).detect(self.pud_doc_assets)
        
        return ui_render, kb
    
    def _validate_assemble(self, br_cl, br_pud, doms, kb):
        return None
    
        list_validator = FilelistValidator(self.collector).validate_clank(clank_doms, self.clank_doc_assets, self.clank_cfg)
        list_validator.validate_pud(pud_doms, self.pud_doc_assets, self.pud_cfg) 
        
        fileset_validator = FilesetValidator(self.collector).validate_clank(clank_doms, self.clank_doc_assets, self.clank_cfg)
        fileset_validator.validate_pud(pud_doms, self.pud_doc_assets, self.pud_cfg)      

        CollisionDetector(self.collector).detect(self.clank_doc_assets) 
        CollisionDetector(self.collector).detect(self.pud_doc_assets)
    

        