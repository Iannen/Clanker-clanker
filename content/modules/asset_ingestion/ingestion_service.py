from stdlib import dataclass, StrEnum, field
from core import (
    CorruptClanker,
    ClankerAssets,
    PudAssets,
    PathTokens,
    RepoContract,
    Config,
    AssetPack,
    Filereq,
    RepoItem
)
from core.engine_deps import IngestionService, NoSuchFile, AssetExists, DiskPort, ConfigParseError, ConfigParserPort, StartResult, ClankerizeResult, TerminateResult

from . import (
    ErrorCollector,
    FilelistExtractor,
    FilelistMap,
    FilesetMap,
    FilesetExtractor,
    DomainExtractor,
    BaseResolverExtractor,
    SysConfigExtractor,
    FilelistValidator,
    FilesetValidator,
    CollisionDetector,
    Malformed,
    Missing
)

@dataclass(slots=True)
class IngestionServiceImpl(IngestionService):
    files: DiskPort
    cfg_ingestor: ConfigParserPort

    def _get_asset_pack(self,token:str, roots) -> AssetPack | Missing:
        try: return AssetPack(token, "", roots, self.files.get_dir_manifest(token, roots)) 
        except NoSuchFile: return Missing(token, roots) 

    def _get_config(self, config: StrEnum) -> Config | Missing | Malformed:
        try:
            raw_content = self.files.get_file_contents(config.value)
            return Config(config.name, config.value, self.cfg_ingestor.get_as_dict(raw_content))
        except NoSuchFile: return Missing(config.name, config.value)
        except ConfigParseError as ex: return Malformed(config.name, config.value, str(ex))

    def _get_file_req(self, filereq: StrEnum) -> Filereq | Missing:
        try: return Filereq(filereq.name, filereq.value, self.files.get_file_contents(filereq.value))
        except IsADirectoryError: return Filereq(filereq.name, filereq.value, "") 
        except NoSuchFile: return Missing(filereq.name, filereq.value) 

    def get_runtime_config(self):
        ec = ErrorCollector()
        clank_classifier = ItemClassifier(ec)
        pud_classifier = ItemClassifier(ec)

        for req in [*ClankerAssets.templates, *ClankerAssets.layouts]: clank_classifier.classify(self._get_file_req(req))
        for req in [*PudAssets.Directories, *PudAssets.Files, *PudAssets.Documentation]: pud_classifier.classify(self._get_file_req(req))

        assember = Assembler(
            ec, 
            clank_classifier.classify(self._get_config(ClankerAssets.Configs.shared_cfg)),
            clank_classifier.classify(self._get_config(ClankerAssets.Configs.sys_cfg)),
            clank_classifier.classify(self._get_asset_pack(PathTokens.SHARED, ["content/a_lib"])),
            pud_classifier.classify(self._get_config(PudAssets.Configs.configuration_file)), 
            pud_classifier.classify(self._get_asset_pack(PathTokens.PUD, [".clanker"])), 
            pud_classifier.classify(self._get_asset_pack(PathTokens.PUD, ["content", "README.md"])), 
        )
        clank_classifier.complain() 
        pud_result = pud_classifier.evaluate()
        if pud_result is ClassificationResult.MIXED: pud_classifier.complain() 
        ui_render, kb = assember.assemble(pud_result)

        
        if ec.has_crits(): return TerminateResult(ec) 
        if pud_result is ClassificationResult.ALL_PRESENT: return StartResult(ec, kb, ui_render) 
        if pud_result is ClassificationResult.NONE_PRESENT: return ClankerizeResult(ec)
        
    def initialize_workspace(self):
        if self.files.is_cwd_script_dir():
            raise CorruptClanker("Clanker repository initialized is beyond scope of app.")
        for dir_path in RepoContract.DIRS_TO_CREATE:
            self.files.create_dir(dir_path)

        for from_path, to_path in RepoContract.MAPPINGS:
            self.files.copy_file(from_path=from_path, to_path=to_path)
        return self.get_runtime_config()

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

    # not sure about value of the pud res in here.
    def assemble(self, pud_res: ClassificationResult) ->  tuple[BootAction, Render, Keyboard]:
        clank_fl, pud_fl = FilelistExtractor(self.collector).get_filelists(self.clank_cfg, self.pud_cfg)
        clank_fs, pud_fs = FilesetExtractor(self.collector).get_filesets(self.clank_cfg, self.pud_cfg)
        pud_baseres = BaseResolverExtractor(self.collector).get_base_res(self.clank_cfg, self.pud_cfg, clank_fl, pud_fl)
        clank_doms, pud_doms = DomainExtractor(self.collector).get_domains(self.clank_cfg, clank_fs, clank_fl, self.pud_cfg, pud_fs, pud_fl, pud_baseres)
        ui_render, kb = SysConfigExtractor(self.collector, self.sys_cfg).get_final_product(clank_doms, pud_doms)       

        list_validator = FilelistValidator(self.collector).validate_clank(clank_doms, self.clank_doc_assets, self.clank_cfg)
        list_validator.validate_pud(pud_doms, self.pud_doc_assets, self.pud_cfg) 
        
        fileset_validator = FilesetValidator(self.collector).validate_clank(clank_doms, self.clank_doc_assets, self.clank_cfg)
        fileset_validator.validate_pud(pud_doms, self.pud_doc_assets, self.pud_cfg)      

        CollisionDetector(self.collector).detect(self.clank_doc_assets) 
        CollisionDetector(self.collector).detect(self.pud_doc_assets)

        return ui_render, kb
