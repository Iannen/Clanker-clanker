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
        clank = ClankerCtx(
            sys_cfg = self._get_config(ClankerAssets.Configs.sys_cfg),
            shared_cfg = self._get_config(ClankerAssets.Configs.shared_cfg),
            doc_assets = self._get_asset_pack(PathTokens.SHARED, ["content/a_lib"]),
            file_reqs = self._get_file_reqs([*ClankerAssets.Templates, *ClankerAssets.Layouts])
        )
        collector, res = clank.determine_action()

        pud = PudCtx(
            pud_cfg = self._get_config(PudAssets.Configs.configuration_file),
            doc_assets = self._get_asset_pack(PathTokens.PUD, [".clanker"]),
            content_assets = self._get_asset_pack(PathTokens.PUD, ["content", "README.md"]),
            file_reqs = self._get_file_reqs([*PudAssets.Directories, *PudAssets.Files, *PudAssets.Documentation]),
            collector = collector,
            clank_res=res
        )

        collector, ui_render, kb, action  = pud.determine_action()
       

        if collector.has_crits(): return TerminateResult(collector)
        elif action is BootAction.CLANKERIZE: return ClankerizeResult(collector)
        elif action is BootAction.START: return StartResult(collector, kb, ui_render) 
                          
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
    sys_cfg: Config | Missing | Malformed
    shared_cfg: Config | Missing | Malformed
    doc_assets: AssetPack | Missing
    file_reqs: tuple[list[StrEnum], list[StrEnum]]
    collector: ErrorCollector = field(default_factory=ErrorCollector)

    def determine_action(self):
        missing_items, present_items, malformed_items = *self.file_reqs, []
        sys_cfg = self._classify(self.sys_cfg, malformed_items, missing_items, present_items)
        shared_cfg = self._classify(self.shared_cfg, malformed_items, missing_items, present_items)
        doc_assets = self._classify(self.doc_assets, malformed_items, missing_items, present_items)
        for item in missing_items + malformed_items: self.collector.accept(item)

        sys_valid = isinstance(sys_cfg, Config)
        shared_data = shared_cfg.data if isinstance(shared_cfg, Config) else None
        filelist = FilelistExtractor(self.collector).extract(shared_cfg) if shared_data else None
        fileset = FilesetExtractor(self.collector).extract(shared_cfg) if shared_data else None
        shared_doms = DomainExtractor(self.collector, fileset, filelist).extract(shared_cfg) if shared_data else None
        sys_cfg_extractor = SysConfigExtractor(self.collector, sys_cfg)
        sys_cfg_extractor.accept_shared_doms(shared_doms)
        base_res = BaseResolverExtractor(self.collector, filelist).extract(shared_cfg) if shared_data else None

        if doc_assets: CollisionDetector(self.collector).detect(doc_assets)
        #return (sys_cfg_extractor, base_res, shared_doms, self.collector), (filelist, fileset) #. the former for service, the latter for pud
        return self.collector, (sys_cfg_extractor, base_res, shared_doms, filelist, fileset, doc_assets, shared_cfg) 



@dataclass
class PudCtx(ItemHandler):
    pud_cfg: Config | Missing | Malformed
    doc_assets: AssetPack | Missing
    content_assets: AssetPack | Missing
    file_reqs: tuple[list[StrEnum], list[StrEnum]]
    collector: ErrorCollector
    clank_res: Any

    def determine_action(self):        
        missing_items, present_items, malformed_items = *self.file_reqs, []
        pud_cfg = self._classify(self.pud_cfg, malformed_items, missing_items, present_items)
        doc_assets = self._classify(self.doc_assets, malformed_items, missing_items, present_items)
        content_assets = self._classify(self.content_assets, malformed_items, missing_items, present_items)
        action = BootAction.NONE
        if not missing_items and not malformed_items: action = BootAction.START
        elif not present_items: action = BootAction.CLANKERIZE
        else: [self.collector.accept(item) for item in missing_items + malformed_items]

        sys_cfg_extractor, clank_base_res, clank_doms, clank_filelist, clank_fileset, clank_doc_assets, shared_cfg = self.clank_res

        unified_filelist = FilelistExtractor(self.collector).extract(pud_cfg, clank_filelist) if pud_cfg else None
        unified_fileset = FilesetExtractor(self.collector).extract(pud_cfg, clank_fileset) if pud_cfg else None
        pud_base_res = BaseResolverExtractor(self.collector, unified_filelist).extract(pud_cfg) if pud_cfg else None
        base_resolver = pud_base_res if pud_base_res else clank_base_res
        if isinstance(doc_assets, AssetPack): CollisionDetector(self.collector).detect(doc_assets)
        
        pud_doms = DomainExtractor(self.collector, unified_fileset, unified_filelist).extract(pud_cfg) if unified_filelist and unified_fileset and isinstance(pud_cfg, Config) else None
        for d in [d for doms in (clank_doms, pud_doms) if doms for d in doms if d is not None]:
                    for res in d.resolvers:
                        d.resolvers = base_resolver +d.resolvers
        sys_cfg_extractor.accept_pud_doms(pud_doms)
        ui_render, kb = sys_cfg_extractor.deliver()

        #for d in [d for doms in (shared_doms, pud_doms) if doms for d in doms if d is not None]:
            #   for res in d.resolvers:
            #      d.resolvers = base_resolver +d.resolvers
        # TODO arg/param alignment. this must happen after base resolver injection. the correct base resolver isnt discovered untill after both pud and clank have been processed
        (FilelistValidator(doc_assets, clank_doc_assets)
        .validate(pud_cfg, pud_doms, self.collector)
        .validate(shared_cfg, clank_doms, self.collector))
        
        """
        TODO arg/param alignment
        (FilesetValidator(pud_ctx.content_assets, clank_ctx.doc_assets)
        .validate(pud_res.pud_cfg, pud_doms, collector)
        .validate(clank_ctx.shared_cfg, clank_ctx.doms, clank_ctx.collector))
        """
        return self.collector, ui_render, kb, action

        #return self.collector, unified_filelist, unified_fileset, base_resolver, pud_cfg, action