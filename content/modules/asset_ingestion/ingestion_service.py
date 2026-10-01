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
            cfg_result = self._get_config(PudAssets.Configs.configuration_file),
            doc_assets_result = self._get_asset_pack(PathTokens.PUD, [".clanker"]),
            content_assets_result = self._get_asset_pack(PathTokens.PUD, ["content", "README.md"]),
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
        cfg = self._classify(self.shared_cfg, malformed_items, missing_items, present_items)
        doc_assets = self._classify(self.doc_assets, malformed_items, missing_items, present_items)
        for item in missing_items + malformed_items: self.collector.accept(item)

        filelist, filelist_extractor = FilelistExtractor(self.collector).clank_fl(cfg)
        fileset, fileset_extractor = FilesetExtractor(self.collector).clank_fs(cfg)
        doms, dom_extractor = DomainExtractor(self.collector, fileset, filelist).extract_shared_doms(cfg, fileset, filelist)
        # here I must validate that doms can source from fileset and filelist
        # this then satisfies that clank does not rely on pud

        sys_cfg_extractor = SysConfigExtractor(self.collector, sys_cfg)
        sys_cfg_extractor.accept_shared_doms(doms)

        base_res, base_res_extractor = BaseResolverExtractor(self.collector, filelist).extract_from_clanker(cfg, filelist)
        # I need to verify that this base_res can source from clanker assets.

        if doc_assets: CollisionDetector(self.collector).detect(doc_assets)
        return self.collector, (sys_cfg_extractor, filelist_extractor, fileset_extractor, base_res_extractor, dom_extractor, doc_assets, cfg) 



@dataclass
class PudCtx(ItemHandler):
    cfg_result: Config | Missing | Malformed
    doc_assets_result: AssetPack | Missing
    content_assets_result: AssetPack | Missing
    file_reqs: tuple[list[StrEnum], list[StrEnum]]
    collector: ErrorCollector
    clank_res: Any

    def determine_action(self):        
        # hm, could I put all my items in some list, and pass a list to classify? then it returns the item or none in a new list
        missing_items, present_items, malformed_items = *self.file_reqs, []
        cfg = self._classify(self.cfg_result, malformed_items, missing_items, present_items)
        doc_assets = self._classify(self.doc_assets_result, malformed_items, missing_items, present_items)
        content_assets = self._classify(self.content_assets_result, malformed_items, missing_items, present_items)
        action = BootAction.NONE
        if not missing_items and not malformed_items: action = BootAction.START
        elif not present_items: action = BootAction.CLANKERIZE
        else: [self.collector.accept(item) for item in missing_items + malformed_items]

        return self._process((cfg, doc_assets, content_assets, action))

    
    def _process(self, inputs):
        cfg, doc_assets, content_assets, action = inputs

        sys_cfg_extractor, filelist_extractor, fileset_extractor, base_res_extractor, dom_extractor, clank_doc_assets, shared_cfg = self.clank_res

        filelist = filelist_extractor.unified_fl(cfg)
        filesets = fileset_extractor.unified_fs(cfg)
        base_resolver = base_res_extractor.get_proper_baseres(cfg, filelist)
        # i must verify that the resolver returned can be satisfied with regards to the files it relies on.
        pud_doms, clank_doms = dom_extractor.extract_and_return_both(cfg, filesets, filelist, base_resolver)
        sys_cfg_extractor.accept_pud_doms(pud_doms)
        ui_render, kb = sys_cfg_extractor.deliver()

        if isinstance(doc_assets, AssetPack): CollisionDetector(self.collector).detect(doc_assets)
        # TODO arg/param alignment. this must happen after base resolver injection. the correct base resolver isnt discovered untill after both pud and clank have been processed
        (FilelistValidator(doc_assets, clank_doc_assets)
        .validate(cfg, pud_doms, self.collector)
        .validate(shared_cfg, clank_doms, self.collector))
        
        """
        TODO arg/param alignment
        (FilesetValidator(pud_ctx.content_assets, clank_ctx.doc_assets)
        .validate(pud_res.pud_cfg, pud_doms, collector)
        .validate(clank_ctx.shared_cfg, clank_ctx.doms, clank_ctx.collector))
        """
        return self.collector, ui_render, kb, action
