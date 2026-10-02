from stdlib import dataclass, StrEnum, field
from core import (
    CorruptClanker,
    ClankerAssets,
    PudAssets,
    PathTokens,
    RepoContract,
    Config,
    AssetPack,
    Filereq
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

    def _get_asset_pack(self,token:str, roots):
        try: return AssetPack(token, roots, self.files.get_dir_manifest(token, roots)) 
        except NoSuchFile: return Missing(token, roots) 

    def _get_config(self, config: StrEnum) -> Config | MissingConfig | MalformedConfig:
        try:
            raw_content = self.files.get_file_contents(config.value)
            return Config(config.name, config.value, self.cfg_ingestor.get_as_dict(raw_content))
        except NoSuchFile: return Missing(config.name, config.value)
        except ConfigParseError: return Malformed(config.name, config.value, str(ex))
    
    def _get_file_reqs(self, assets: list[StrEnum]) -> tuple[list[StrEnum], list[StrEnum]]:
        missing, present = [], []
        for asset in assets:
            try:
                self.files.assert_absent(asset)
                missing.append(Missing(asset.name, asset.value))
            except AssetExists:
                present.append(Filereq(asset.name, asset.value))
        return missing, present

    def get_runtime_config(self):
        collector = ErrorCollector()
        clank = ClankerCtx(
            collector=collector,
            sys_cfg = self._get_config(ClankerAssets.Configs.sys_cfg),
            shared_cfg = self._get_config(ClankerAssets.Configs.shared_cfg),
            doc_assets = self._get_asset_pack(PathTokens.SHARED, ["content/a_lib"]),
            file_reqs = self._get_file_reqs([*ClankerAssets.Templates, *ClankerAssets.Layouts])
        )
        pud = PudCtx(
            collector = collector,
            cfg_result = self._get_config(PudAssets.Configs.configuration_file),
            doc_assets_result = self._get_asset_pack(PathTokens.PUD, [".clanker"]),
            content_assets_result = self._get_asset_pack(PathTokens.PUD, ["content", "README.md"]),
            file_reqs = self._get_file_reqs([*PudAssets.Directories, *PudAssets.Files, *PudAssets.Documentation]),
        )
        action, ui_render, kb = Assembler.assemble(collector, clank.determine_action(), pud.determine_action())

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

class ItemHandler:
    def _classify(self,item ,malformed_items ,missing_items, present_items):
        if isinstance(item, (Config, AssetPack)): present_items.append(item); return item
        if isinstance(item, Malformed):malformed_items.append(item)
        elif isinstance(item, (Missing)):missing_items.append(item)
        return None

@dataclass
class ClankerCtx(ItemHandler):
    collector: ErrorCollector
    sys_cfg: Config | Missing | Malformed
    shared_cfg: Config | Missing | Malformed
    doc_assets: AssetPack | Missing
    file_reqs: tuple[list[StrEnum], list[StrEnum]]

    def determine_action(self):
        missing_items, present_items, malformed_items = *self.file_reqs, []
        sys_cfg = self._classify(self.sys_cfg, malformed_items, missing_items, present_items)
        cfg = self._classify(self.shared_cfg, malformed_items, missing_items, present_items)
        doc_assets = self._classify(self.doc_assets, malformed_items, missing_items, present_items)
        for item in missing_items + malformed_items: self.collector.accept(item)

        return cfg, sys_cfg, doc_assets


@dataclass
class PudCtx(ItemHandler):
    collector: ErrorCollector
    cfg_result: Config | Missing | Malformed
    doc_assets_result: AssetPack | Missing
    content_assets_result: AssetPack | Missing
    file_reqs: tuple[list[StrEnum], list[StrEnum]]

    def determine_action(self):        
        missing_items, present_items, malformed_items = *self.file_reqs, []
        cfg = self._classify(self.cfg_result, malformed_items, missing_items, present_items)
        doc_assets = self._classify(self.doc_assets_result, malformed_items, missing_items, present_items)
        content_assets = self._classify(self.content_assets_result, malformed_items, missing_items, present_items)
        action = BootAction.NONE
        if not missing_items and not malformed_items: action = BootAction.START
        elif not present_items: action = BootAction.CLANKERIZE
        else: [self.collector.accept(item) for item in missing_items + malformed_items]
        return cfg, doc_assets, content_assets, action

@dataclass
class Assembler:
    @staticmethod
    def assemble(collector: ErrorCollector, clank_inputs, pud_inputs) ->  tuple[BootAction, Render, Keyboard]:
        clank_cfg, sys_cfg, clank_doc_assets = clank_inputs
        pud_cfg, pud_doc_assets, pud_content_assets, action  = pud_inputs

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

        return action, ui_render, kb