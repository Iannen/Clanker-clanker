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

    """ the service use these 3 methods to convert a strenum to a proper item or a complaint """
    def _get_asset_pack(self,token:str, roots) -> AssetPack | Missing:
        try: return AssetPack(token, roots, self.files.get_dir_manifest(token, roots)) 
        except NoSuchFile: return Missing(token, roots) 

    def _get_config(self, config: StrEnum) -> Config | Missing | Malformed:
        try:
            raw_content = self.files.get_file_contents(config.value)
            return Config(config.name, config.value, self.cfg_ingestor.get_as_dict(raw_content))
        except NoSuchFile: return Missing(config.name, config.value)
        except ConfigParseError: return Malformed(config.name, config.value, str(ex))

    def _get_file_req(self, filereq: StrEnum) -> Filereq | Missing:
        try: return Filereq(filereq.name, filereq.value, self.files.get_file_contents(filereq.value))
        except NoSuchFile: return Missing(filereq.name, filereq.value) 

    def _classify_file_reqs(self, assets: list[StrEnum]) -> tuple[list[StrEnum], list[StrEnum]]:
        """ this method gets converted to work on a single strenum at a time""" 
        missing, present = [], []
        for asset in assets:
            try:
                self.files.assert_absent(asset)
                missing.append(Missing(asset.name, asset.value))
            except AssetExists:
                present.append(Filereq(asset.name, asset.value, ""))
        return missing, present

    def _evaluate_clanker_items(self):pass
    """ 
    - 'important' items via separate args, return the item | None
    - the unimportant ones i get in a list for bulk processing
        i implement whater business rules i have for clankers items here
    """

    def _evaluate_pud_items(self):pass
    """ 'important' items via separate params, the unimportant ones in a list"""

    def get_runtime_config(self):
        collector = ErrorCollector()
        present, missing, malformed = [], [], []
        sys_cfg = Classifier._classify(self._get_config(ClankerAssets.Configs.sys_cfg),present, missing, malformed)
        shared_cfg = Classifier._classify(self._get_config(ClankerAssets.Configs.shared_cfg),present, missing, malformed)
        doc_assets = Classifier._classify(self._get_asset_pack(PathTokens.SHARED, ["content/a_lib"]),present, missing, malformed)
        for req in [*ClankerAssets.Templates, *ClankerAssets.Layouts]: Classifier._classify(self._get_file_req(req), present, missing, malformed)

        
        clank = ClankerCtx.determine_action(
            collector=collector,
            sys_cfg = self._get_config(ClankerAssets.Configs.sys_cfg),
            shared_cfg = self._get_config(ClankerAssets.Configs.shared_cfg),
            doc_assets = self._get_asset_pack(PathTokens.SHARED, ["content/a_lib"]),
            file_reqs = self._classify_file_reqs([*ClankerAssets.Templates, *ClankerAssets.Layouts])
        )
        pud = PudCtx.determine_action(
            collector = collector,
            cfg_result = self._get_config(PudAssets.Configs.configuration_file),
            doc_assets_result = self._get_asset_pack(PathTokens.PUD, [".clanker"]),
            content_assets_result = self._get_asset_pack(PathTokens.PUD, ["content", "README.md"]),
            file_reqs = self._classify_file_reqs([*PudAssets.Directories, *PudAssets.Files, *PudAssets.Documentation]),
        )
        
        action, ui_render, kb = Assembler.assemble(collector, clank, pud)

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

class Classifier:
    @staticmethod
    def _classify(item, malformed_items, missing_items, present_items):
        if isinstance(item, (Config, AssetPack)): present_items.append(item); return item # common ancestor for these kinda items in the future
        if isinstance(item, Malformed): malformed_items.append(item)
        elif isinstance(item, Missing): missing_items.append(item)
        return None

class ClankerCtx(Classifier):
    @staticmethod
    def determine_action(
        collector: ErrorCollector, 
        sys_cfg: Config | Missing | Malformed, 
        shared_cfg: Config | Missing | Malformed, 
        doc_assets: AssetPack | Missing, 
        file_reqs: tuple[list[StrEnum], list[StrEnum]]
    ) -> tuple [Config | None, Config | None, AssetPack | None]:
        missing_items, present_items, malformed_items = *file_reqs, []
        sys_cfg = ClankerCtx._classify(sys_cfg, malformed_items, missing_items, present_items)
        cfg = ClankerCtx._classify(shared_cfg, malformed_items, missing_items, present_items)
        doc_assets = ClankerCtx._classify(doc_assets, malformed_items, missing_items, present_items)
        for item in missing_items + malformed_items: collector.accept(item)
        return cfg, sys_cfg, doc_assets

class PudCtx(Classifier):
    @staticmethod
    def determine_action(
        collector: ErrorCollector, 
        cfg_result: Config | Missing | Malformed, 
        doc_assets_result: AssetPack | Missing, 
        content_assets_result: AssetPack | Missing, 
        file_reqs: tuple[list[StrEnum], list[StrEnum]]
    ) -> tuple [Config | None, AssetPack | None, AssetPack | None, BootAction]:
        missing_items, present_items, malformed_items = *file_reqs, []
        cfg = PudCtx._classify(cfg_result, malformed_items, missing_items, present_items)
        doc_assets = PudCtx._classify(doc_assets_result, malformed_items, missing_items, present_items)
        content_assets = PudCtx._classify(content_assets_result, malformed_items, missing_items, present_items)
        action = BootAction.NONE
        if not missing_items and not malformed_items: action = BootAction.START
        elif not present_items: action = BootAction.CLANKERIZE
        else: [collector.accept(item) for item in missing_items + malformed_items]
        return cfg, doc_assets, content_assets, action

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