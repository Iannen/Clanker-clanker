from stdlib import dataclass, StrEnum, field
from core import (
    CorruptClanker,
    ClankerAssets,
    PudAssets,
    PathTokens,
    RepoContract,
    DictConfig,
    MissingConfig,
    AssetPack,
    MalformedConfig,
    MissingAssetPack,
)
from core.engine_deps import IngestionService, NoSuchFile, AssetExists, DiskPort, ConfigParseError, ConfigParserPort, StartResult, ClankerizeResult, TerminateResult

from . import (
    ErrorCollector,
    FilelistExtractor,
    FilesetExtractor,
    DomainExtractor,
    BaseResolverExtractor,
    UIRenderExtractor,
    RtcAssembler,
    FilelistValidator,
    FilesetValidator,
    CollisionDetector,
)
class BootAction(StrEnum):
    START = "ok"
    CLANKERIZE = "empty"
    NONE = "invalid"

@dataclass
class ClankerCtx:
    sys_cfg: Config
    shared_cfg: Config
    doc_assets: AssetPack
    file_reqs: tuple[list[StrEnum], list[StrEnum]]
    collector: ErrorCollector = field(default_factory=ErrorCollector)

    def _determine_action(self):
        absent_files, present_files = self.file_reqs
        configs = [self.sys_cfg, self.shared_cfg]
        assetpacks = [self.doc_assets]

        if not absent_files and all(isinstance(cfg, DictConfig) for cfg in configs) and all(pack.issue is None for pack in assetpacks):
            self.action = BootAction.START
        else: 
            self.action = BootAction.NONE
            for missing_file in absent_files: self.collector.add_critical_complaint(f"'{missing_file.name}' not found at '{missing_file.value}'")            
            for missing_cfg in [cfg for cfg in configs if isinstance(cfg, MissingConfig)]: self.collector.add_critical_complaint(f"'{missing_cfg.name}' not found at '{missing_cfg.path}'")
            for malformed in [cfg for cfg in configs if isinstance(cfg, MalformedConfig)]: self.collector.add_critical_complaint(f"'{malformed.name}' not found at '{malformed.path}'")

    def process(self):
        self._determine_action()
        self.ui_render = UIRenderExtractor(self.collector).extract(self.sys_cfg) if self.sys_cfg.data else None
        self.filelist = FilelistExtractor(self.collector).extract(self.shared_cfg) if self.shared_cfg.data else None
        self.fileset = FilesetExtractor(self.collector).extract(self.shared_cfg) if self.shared_cfg.data else None
        self.doms = DomainExtractor(self.collector, self.fileset, self.filelist).extract(self.shared_cfg) if self.shared_cfg.data else None
        self.base_res = BaseResolverExtractor(self.collector, self.fileset, self.filelist).extract(self.shared_cfg) if self.shared_cfg.data else None
        if self.doc_assets.paths: CollisionDetector(self.collector).detect(self.doc_assets) 

@dataclass
class PudCtx:
    pud_cfg: Config
    doc_assets: AssetPack
    content_assets: AssetPack
    file_reqs: tuple[list[StrEnum], list[StrEnum]]
    collector: ErrorCollector = field(default_factory=ErrorCollector)

    def _determine_action(self):
        absent_files, present_files = self.file_reqs # this splits a list of name, value strenums into two lists, depending on disk presence
        configs = [self.pud_cfg]
        assetpacks = [self.doc_assets, self.content_assets]

        if not absent_files and all(isinstance(cfg, DictConfig) for cfg in configs) and all(pack.issue is None for pack in assetpacks):
            self.action = BootAction.START
        elif not present_files and all(isinstance(cfg, MissingConfig) for cfg in configs) and all(pack.issue is not None for pack in assetpacks):
            self.action = BootAction.CLANKERIZE
        else: 
            self.action = BootAction.NONE
            for missing_file in absent_files: self.collector.add_critical_complaint(f"'{missing_file.name}' not found at '{missing_file.value}'")            
            for missing_cfg in [cfg for cfg in configs if isinstance(cfg, MissingConfig)]: self.collector.add_critical_complaint(f"'{missing_cfg.name}' not found at '{missing_cfg.path}'")
            for malformed in [cfg for cfg in configs if isinstance(cfg, MalformedConfig)]: self.collector.add_critical_complaint(f"'{malformed.name}' not found at '{malformed.path}'")

    def process(self):
        self._determine_action()
        cfg = isinstance(self.pud_cfg, DictConfig)
        self.filelist = FilelistExtractor(self.collector).extract(self.pud_cfg) if cfg else None
        self.fileset = FilesetExtractor(self.collector).extract(self.pud_cfg) if cfg else None
        if self.doc_assets.paths: CollisionDetector(self.collector).detect(self.doc_assets)

@dataclass(slots=True)
class IngestionServiceImpl(IngestionService):
    files: DiskPort
    cfg_ingestor: ConfigParserPort

    def _get_asset_pack(self,token:str, roots) -> AssetPack:
        try:
            return AssetPack(token, roots, self.files.get_dir_manifest(token, roots)) 
        except NoSuchFile:
            return AssetPack(token, roots, None, f"Something missing in '{token}': {roots}") 

    def _get_config(self, config: StrEnum) -> Config:
        try:
            raw_content = self.files.get_file_contents(config.value)
            return DictConfig(config.name, config.value, self.cfg_ingestor.get_as_dict(raw_content))
        except NoSuchFile:
            return MissingConfig(config.name, config.value)
        except ConfigParseError: 
            return MalformedConfig(config.name, config.value, str(ex))
    
    def _get_file_reqs(self, assets: list[StrEnum]) -> tuple[list[StrEnum], list[StrEnum]]:
        missing = []
        present = []
        for asset in assets:
            try:
                self.files.assert_absent(asset)
                missing.append(asset)
            except AssetExists:
                present.append(asset)
        return missing, present

    def get_runtime_config(self):
        clank_ctx = ClankerCtx(
            sys_cfg = self._get_config(ClankerAssets.Configs.sys_cfg),
            shared_cfg = self._get_config(ClankerAssets.Configs.shared_cfg),
            doc_assets = self._get_asset_pack(PathTokens.SHARED, ["content/a_lib"]),
            file_reqs = self._get_file_reqs([*ClankerAssets.Templates, *ClankerAssets.Layouts])
        )
        clank_ctx.process()
        pud_ctx = PudCtx(
            pud_cfg = self._get_config(PudAssets.Configs.configuration_file),
            doc_assets = self._get_asset_pack(PathTokens.PUD, [".clanker"]),
            content_assets = self._get_asset_pack(PathTokens.PUD, ["content", "README.md"]),
            file_reqs = self._get_file_reqs([*PudAssets.Directories, *PudAssets.Files, *PudAssets.Documentation])
        )
        pud_ctx.process()

        merged_collector = ErrorCollector()
        merged_collector.set_complaints(clank_ctx.collector.get_complaints() + pud_ctx.collector.get_complaints())
        merged_collector.set_critical_complaints(clank_ctx.collector.get_critical_complaints() + pud_ctx.collector.get_critical_complaints())
        match (clank_ctx.action, pud_ctx.action, merged_collector.has_crits()):
            case (BootAction.START, BootAction.START, False):

                unified_fsm = clank_ctx.fileset.merge(pud_ctx.fileset)
                unified_flm = clank_ctx.filelist.merge(pud_ctx.filelist)
                pud_doms = DomainExtractor(merged_collector, unified_fsm, unified_flm).extract(pud_ctx.pud_cfg)

                # TODO: try to extract a single resolver from both pud and shared.
                # if any of them supply more than one, softcomplain and pick one. 
                # then here, pick pud over shared and use that
                for dom in pud_doms+clank_ctx.doms:
                    dom.resolvers = dom.resolvers + clank_ctx.base_res
                # TODO the buttons should be dealt with by the clankerctx at this point
                button_map = RtcAssembler().assemble(
                    sys_cfg=clank_ctx.sys_cfg,
                    shared_doms=clank_ctx.doms,
                    pud_doms=pud_doms,
                    collector=merged_collector,
                )
                # TODO arg/param alignment
                (FilelistValidator(pud_ctx.doc_assets, clank_ctx.doc_assets)
                .validate(pud_ctx.pud_cfg, pud_doms, pud_ctx.collector)
                .validate(clank_ctx.shared_cfg, clank_ctx.doms, clank_ctx.collector))
                
                """
                TODO arg/param alignment
                (FilesetValidator(pud_ctx.content_assets, clank_ctx.doc_assets)
                .validate(pud_ctx.pud_cfg, pud_doms, pud_ctx.collector)
                .validate(clank_ctx.shared_cfg, clank_ctx.doms, clank_ctx.collector))
                """
                return StartResult(merged_collector, button_map, clank_ctx.ui_render, clank_ctx.base_res)

            case (BootAction.START, BootAction.CLANKERIZE, False):
                return ClankerizeResult(merged_collector)
            case (_, _, True):
                return TerminateResult(merged_collector)
    
    def initialize_workspace(self):
        if self.files.is_cwd_script_dir():
            raise CorruptClanker("Clanker repository initialized is beyond scope of app.")
        for dir_path in RepoContract.DIRS_TO_CREATE:
            self.files.create_dir(dir_path)

        for from_path, to_path in RepoContract.MAPPINGS:
            self.files.copy_file(from_path=from_path, to_path=to_path)
        return self.get_runtime_config()