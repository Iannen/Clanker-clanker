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
        except ConfigParseError: return Malformed(config.name, config.value, str(ex))

    def _get_file_req(self, filereq: StrEnum) -> Filereq | Missing:
        try: return Filereq(filereq.name, filereq.value, self.files.get_file_contents(filereq.value))
        except IsADirectoryError: return Filereq(filereq.name, filereq.value, "") 
        except NoSuchFile: return Missing(filereq.name, filereq.value) 

    def get_runtime_config(self):
        collector = ErrorCollector()
        clank_classifier = ItemClassifier(collector)
        pud_classifier = ItemClassifier(collector)

        for req in [*ClankerAssets.Templates, *ClankerAssets.Layouts]: clank_classifier.classify(self._get_file_req(req))
        for req in [*PudAssets.Directories, *PudAssets.Files, *PudAssets.Documentation]: pud_classifier.classify(self._get_file_req(req))

        ui_render, kb = Assembler.assemble(
            collector, 
            clank_classifier.classify(self._get_config(ClankerAssets.Configs.shared_cfg)),
            clank_classifier.classify(self._get_config(ClankerAssets.Configs.sys_cfg)),
            clank_classifier.classify(self._get_asset_pack(PathTokens.SHARED, ["content/a_lib"])),
            pud_classifier.classify(self._get_config(PudAssets.Configs.configuration_file)), 
            pud_classifier.classify(self._get_asset_pack(PathTokens.PUD, [".clanker"])), 
            pud_classifier.classify(self._get_asset_pack(PathTokens.PUD, ["content", "README.md"])), 
        )

        clank_classifier.complain()

        if pud_classifier.all_present(): action = BootAction.START
        elif pud_classifier.none_present(): action = BootAction.CLANKERIZE
        else:  action = BootAction.NONE ; pud_classifier.complain()
       
        if collector.has_crits(): return TerminateResult(collector)
        if action is BootAction.CLANKERIZE: return ClankerizeResult(collector)
        if action is BootAction.START: return StartResult(collector, kb, ui_render) 
                          
    def initialize_workspace(self):
        if self.files.is_cwd_script_dir():
            raise CorruptClanker("Clanker repository initialized is beyond scope of app.")
        for dir_path in RepoContract.DIRS_TO_CREATE:
            self.files.create_dir(dir_path)

        for from_path, to_path in RepoContract.MAPPINGS:
            self.files.copy_file(from_path=from_path, to_path=to_path)
        return self.get_runtime_config()

class BootAction(StrEnum):
    START = "ok"
    CLANKERIZE = "empty"
    NONE = "invalid"

class ItemClassifier:
    def __init__(self, ec: ErrorCollector):
        self.ec = ec
        self.present, self.missing, self.malformed = [],[],[]
    def classify(self, item):
        if isinstance(item, RepoItem): self.present.append(item); return item 
        if isinstance(item, Missing): self.missing.append(item); return None
        if isinstance(item, Malformed): self.malformed.append(item) ; return None
    def all_present(self): return not self.missing and not self.malformed
    def none_present(self): return not self.present
    def complain(self):
        for c in self.missing + self.malformed: self.ec.accept(c)

class Assembler:
    @staticmethod
    def assemble(
        collector: ErrorCollector, 
        clank_cfg,
        sys_cfg,
        clank_doc_assets,
        pud_cfg, 
        pud_doc_assets, 
        pud_content_assets, 
    ) ->  tuple[BootAction, Render, Keyboard]:

        clank_fl, pud_fl = FilelistExtractor(collector).get_filelists(clank_cfg, pud_cfg)
        clank_fs, pud_fs = FilesetExtractor(collector).get_filesets(clank_cfg, pud_cfg)
        pud_baseres = BaseResolverExtractor(collector).get_base_res(clank_cfg, pud_cfg, clank_fl, pud_fl)
        clank_doms, pud_doms = DomainExtractor(collector).get_domains(clank_cfg, clank_fs, clank_fl, pud_cfg, pud_fs, pud_fl, pud_baseres)
        ui_render, kb = SysConfigExtractor(collector, sys_cfg).get_final_product(clank_doms, pud_doms)       

        list_validator = FilelistValidator(collector).validate_clank(clank_doms, clank_doc_assets, clank_cfg)
        list_validator.validate_pud(pud_doms, pud_doc_assets, pud_cfg) 
        
        fileset_validator = FilesetValidator(collector).validate_clank(clank_doms, clank_doc_assets, clank_cfg)
        fileset_validator.validate_pud(pud_doms,pud_doc_assets, pud_cfg)      

        CollisionDetector(collector).detect(clank_doc_assets) 
        CollisionDetector(collector).detect(pud_doc_assets)

        return ui_render, kb
