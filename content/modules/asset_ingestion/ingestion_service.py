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
        a, b = clank.determine_action()
        ui_render, base_res, shared_doms, collector = a
        filelist, fileset = b
        # here I receive a (ui_render, (to pud)) from clank, so pud can finish its business in its lifecycle

        pud = PudCtx(collector)
        pud.determine_action(
            pud_cfg = self._get_config(PudAssets.Configs.configuration_file),
            doc_assets = self._get_asset_pack(PathTokens.PUD, [".clanker"]),
            content_assets = self._get_asset_pack(PathTokens.PUD, ["content", "README.md"]),
            file_reqs = self._get_file_reqs([*PudAssets.Directories, *PudAssets.Files, *PudAssets.Documentation])
        )
        pud.process()

        # then from pud I receive a tuple of only the shit I need to proceed. I can have a third assembler type too, or let the service be the assembler via a helper

        merged_collector = collector.merge(pud.collector)

        merged_filelist = filelist.merge(pud.filelist) if filelist and pud.filelist else None
        merged_fileset = fileset.merge(pud.fileset) if fileset and pud.fileset else None

        base_resolver = pud.base_res if pud.base_res else base_res

        pud_doms = DomainExtractor(merged_collector, merged_fileset, merged_filelist).extract(pud.pud_cfg) if merged_filelist and merged_fileset and base_resolver and isinstance(pud.pud_cfg, Config) else None

        for d in [d for doms in (shared_doms, pud_doms) if doms for d in doms if d is not None]:
            for res in d.resolvers:
                d.resolvers = base_res +d.resolvers

        kb = SysConfigExtractor(merged_collector).get_btn_map(clank.sys_cfg, shared_doms, pud_doms) if isinstance(clank.sys_cfg, Config) and shared_doms and pud_doms else None

        if merged_collector.has_crits(): return TerminateResult(merged_collector)
        elif pud.action is BootAction.CLANKERIZE: return ClankerizeResult(merged_collector)
        elif pud.action is BootAction.START: 
                # TODO arg/param alignment
                (FilelistValidator(pud.doc_assets, clank.doc_assets)
                .validate(pud.pud_cfg, pud_doms, pud.collector)
                .validate(clank.shared_cfg, shared_doms, clank.collector))
                
                """
                TODO arg/param alignment
                (FilesetValidator(pud_ctx.content_assets, clank_ctx.doc_assets)
                .validate(pud_ctx.pud_cfg, pud_doms, pud_ctx.collector)
                .validate(clank_ctx.shared_cfg, clank_ctx.doms, clank_ctx.collector))
                """
                return StartResult(merged_collector, kb, ui_render)            

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
    """
    - produces ui render from sysextractor
    - produces fileset, filelist
    - produces base_resolver
    - produces domains 
    - produces button map, inserts shared domains in it consuming them
    - validates collisions of clank doc assets 
    - returns ui_render, (fileset, filelist, button_map, collector). the former for service, the latter for pud
    """
    sys_cfg: Config | MissingConfig | MalformedConfig
    shared_cfg: Config | MissingConfig | MalformedConfig
    doc_assets: AssetPack | MissingAssetPack
    file_reqs: tuple[list[StrEnum], list[StrEnum]]
    collector: ErrorCollector = field(default_factory=ErrorCollector)

    def determine_action(self,):
        missing_items, present_items, malformed_items = *self.file_reqs, []
        sys_cfg = self._classify(self.sys_cfg, malformed_items, missing_items, present_items)
        shared_cfg = self._classify(self.shared_cfg, malformed_items, missing_items, present_items)
        doc_assets = self._classify(self.doc_assets, malformed_items, missing_items, present_items)
        for item in missing_items + malformed_items: self.collector.accept(item)

        sys_valid = isinstance(sys_cfg, Config)
        shared_data = shared_cfg.data if isinstance(shared_cfg, Config) else None
        ui_render = SysConfigExtractor(self.collector).get_ui_render(sys_cfg) if sys_valid else None
        filelist = FilelistExtractor(self.collector).extract(shared_cfg) if shared_data else None
        fileset = FilesetExtractor(self.collector).extract(shared_cfg) if shared_data else None
        shared_doms = DomainExtractor(self.collector, fileset, filelist).extract(shared_cfg) if shared_data else None
        base_res = BaseResolverExtractor(self.collector, filelist).extract(shared_cfg) if shared_data else None
        # make domains
        if doc_assets: CollisionDetector(self.collector).detect(doc_assets)
        return (ui_render, base_res, shared_doms, self.collector), (filelist, fileset) #. the former for service, the latter for pud

    def process(self): pass


@dataclass
class PudCtx(ItemHandler):
    pud_cfg: Config | None = None
    doc_assets: AssetPack | None = None
    content_assets: AssetPack | None = None
    collector: ErrorCollector = field(default_factory=ErrorCollector)

    def determine_action(
            self,
            pud_cfg: Config | MissingConfig | MalformedConfig,
            doc_assets: AssetPack | MissingAssetPack,
            content_assets: AssetPack | MissingAssetPack,
            file_reqs: tuple[list[StrEnum], list[StrEnum]], 
        ):        
        missing_items, present_items, malformed_items = *file_reqs, []
        self.pud_cfg = self._classify(pud_cfg, malformed_items, missing_items, present_items)
        self.doc_assets = self._classify(doc_assets, malformed_items, missing_items, present_items)
        self.content_assets = self._classify(content_assets, malformed_items, missing_items, present_items)
        self.action = BootAction.NONE
        if not missing_items and not malformed_items: self.action = BootAction.START
        elif not present_items: self.action = BootAction.CLANKERIZE
        else: [self.collector.accept(item) for item in missing_items + malformed_items]

    def process(self):
        self.filelist = FilelistExtractor(self.collector).extract(self.pud_cfg) if self.pud_cfg else None #if cfg else None
        self.fileset = FilesetExtractor(self.collector).extract(self.pud_cfg) if self.pud_cfg else None #if cfg else None
        self.base_res = BaseResolverExtractor(self.collector, self.filelist).extract(self.pud_cfg) if self.pud_cfg else None #if cfg else None
        if isinstance(self.doc_assets, AssetPack): CollisionDetector(self.collector).detect(self.doc_assets)