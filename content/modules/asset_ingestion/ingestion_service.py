from core import (
    NoConfig,
    ConfigAssembly,
    CorruptClanker,
    WorkspaceAlreadyInitialized,
    ClankerAssets,
    PudAssets,
    PathTokens,
    RepoContract,
    ActionResult,
    Button,
    Render,
    Resolver,
    DoBootstrap,
    TerminateGracefully,
    OfferBootstrapWithComplaints,
    OfferClankerize,
    OfferClankerizeWithComplaints,

)
from core.engine_deps import IngestionService, Report, NoSuchFile, AssetExists, DiskPort, ConfigParseError, ConfigParserPort

from . import (
    ErrorCollector,
    UnifiedFilesetExtractor,
    UnifiedFilelistExtractor,
    UnifiedDomainsExtractor,
    FilelistExtractor,
    FilesetExtractor,
    DomainExtractor,
    BaseResolversExtractor,
    UnifiedBaseResolversExtractor,
    UIRenderExtractor,
    RtcAssembler,
    FilelistValidator,
    FilesetValidator,
)

class IngestionServiceImpl(IngestionService):
    def __init__(
        self,
        files: DiskPort,
        cfg_ingestor: ConfigParserPort,
    ) -> None:
        self.files = files
        self.cfg_ingestor = cfg_ingestor

    def _resolve_assets(self, assets: list[StrEnum]) -> tuple[list[StrEnum], list[StrEnum]]:
        missing = []
        present = []
        for asset in assets:
            try:
                self.files.assert_absent(asset)
                missing.append(asset)
            except AssetExists:
                present.append(asset)
        return present, missing

    def _resolve_configs(self, configs: Iterable[StrEnum]):
        cfg_dicts = {}
        missing = []
        malformed = []
        for config in configs:
            try:
                raw_content = self.files.get_file_contents(config.value)
                cfg_dict = self.cfg_ingestor.get_as_dict(raw_content)
                cfg_dict["name"] = config.name
                cfg_dict["src_path"] = config.value
                cfg_dicts[config.name] = cfg_dict
            except NoSuchFile:
                missing.append(config)
            except ConfigParseError:
                malformed.append(config)
        return cfg_dicts, missing, malformed

    def _resolve_clanker_state(self, collector: ErrorCollector) -> tuple[str, dict | None, dict | None]:
        configs, missing, malformed = self._resolve_configs(ClankerAssets.Configs)
        present, missing_assets = self._resolve_assets([*ClankerAssets.Templates, *ClankerAssets.Layouts])
        for cfg in missing: collector.add_critical_complaint(f"Missing clanker asset: {cfg.value}")
        for cfg in malformed: collector.add_critical_complaint(f"Failed to convert clanker config: {cfg.value}")
        for asset_path in missing_assets:collector.add_critical_complaint(f"Missing clanker asset: {asset_path}")
        clanker_state = ClankerAssets.States.BAD if (missing or malformed or missing_assets) else ClankerAssets.States.OK
        return clanker_state, configs

    def _resolve_pud_state(self, collector: ErrorCollector) -> tuple[str, dict | None]:
        configs, missing_cfgs, malformed_cfgs = self._resolve_configs(PudAssets.Configs)
        present, missing_assets = self._resolve_assets([*PudAssets.Directories, *PudAssets.Files, *PudAssets.Documentation])
        if not (missing_cfgs or malformed_cfgs or missing_assets): pud_state = PudAssets.States.OK
        elif not (configs or present): pud_state = PudAssets.States.EMPTY
        else:
            for asset in missing_cfgs + missing_assets: collector.add_critical_complaint(f"Missing pud asset: {asset.name}")
            for cfg in malformed_cfgs: collector.add_critical_complaint(f"Non-convertible pud config: {cfg.name}")
            pud_state = PudAssets.States.BAD
        return pud_state, configs

    def _validate_clanker(self, collector, cfg, sys_cfg):
        """ the stuff we get from clanker """
        filelist = FilelistExtractor(collector).extract(cfg)
        fileset = FilesetExtractor(collector).extract(cfg)
        doms = DomainExtractor(collector, fileset, filelist).extract(cfg)
        base_resolvers = BaseResolversExtractor(collector).extract(cfg)
        ui_render = UIRenderExtractor().extract(sys_cfg, collector, fileset, filelist)
        return collector, filelist, fileset, doms, base_resolvers, ui_render
    def _validate_pud(self, collector, cfg):
        filelist = FilelistExtractor(collector).extract(cfg)
        fileset = FilesetExtractor(collector).extract(cfg)
        return collector, filelist, fileset

    def get_runtime_config(self) -> tuple[ActionResult, Report, dict[str, Button], Render, list[Resolver]]:
        collector = ErrorCollector()

        #these 4 lines shall become 1, yielding clanker state, pud state and configs. 
        clanker_state, clank_cfgs = self._resolve_clanker_state(collector)
        pud_state, pud_cfgs = self._resolve_pud_state(collector)
        repo_state = f"{clanker_state}-{pud_state}"
        configs = {**clank_cfgs, **pud_cfgs}

        # or perhaps we receive a typed object containing these in place of 'configs' dict
        sys_cfg = clank_cfgs.get(ClankerAssets.Configs.sys_cfg.name)
        shared_cfg = clank_cfgs.get(ClankerAssets.Configs.shared_cfg.name)
        pud_cfg = pud_cfgs.get(PudAssets.Configs.PUD.name)

        match (clanker_state, pud_state):
            case (ClankerAssets.States.OK, PudAssets.States.OK):
                _, shared_flm, shared_fsm, shared_doms, base_resolvers, ui_render = self._validate_clanker(collector, shared_cfg, sys_cfg)
                _, pud_flm, pud_fsm = self._validate_pud(collector, pud_cfg)
                unified_fsm = shared_fsm.merge(pud_fsm)
                unified_flm = shared_flm.merge(pud_flm)
                pud_doms = DomainExtractor(collector, unified_fsm, unified_flm).extract(pud_cfg)

                for dom in pud_doms+shared_doms:
                    dom.resolvers = dom.resolvers + base_resolvers
                button_map = RtcAssembler().assemble(
                    sys_cfg=sys_cfg,
                    shared_doms=shared_doms,
                    pud_doms=pud_doms,
                    collector=collector,
                )
                pud_multidoc_assets = pud_fileset_assets = []
                pud_multidoc_assets =self.files.get_dir_manifest(PathTokens.PUD, [".clanker"]) 
                pud_fileset_assets = self.files.get_dir_manifest(PathTokens.PUD, ["content", ".clanker", "README.md"])
                shared_multidoc_assets = self.files.get_dir_manifest(PathTokens.SHARED, ["content/a_lib"])
                FilelistValidator().validate(pud_multidoc_assets, pud_doms, shared_multidoc_assets, shared_doms, collector)                
                shared_fileset_assets = self.files.get_dir_manifest(PathTokens.SHARED, ["content/a_lib"])
                FilesetValidator().validate(pud_fileset_assets, pud_doms, shared_fileset_assets, shared_doms, collector)

                has_soft = bool(collector.get_complaints())
                action_res = OfferBootstrapWithComplaints() if has_soft else DoBootstrap()
                return action_res, collector, button_map, ui_render, base_resolvers
            case (ClankerAssets.States.OK, PudAssets.States.EMPTY):
                self._validate_clanker(collector, shared_cfg, sys_cfg)
                has_soft = bool(collector.get_complaints())
                action_res = OfferClankerizeWithComplaints() if has_soft else OfferClankerize()
                return action_res, collector, None, None, None
            case (ClankerAssets.States.OK, PudAssets.States.BAD):
                self._validate_clanker(collector)
                return TerminateGracefully(), collector, None, None, None
            case (ClankerAssets.States.BAD, PudAssets.States.OK):
                self._validate_pud(collector)
                return TerminateGracefully(), collector, None, None, None
            case (ClankerAssets.States.BAD, PudAssets.States.EMPTY):
                return TerminateGracefully(), collector, None, None, None
            case (ClankerAssets.States.BAD, PudAssets.States.BAD):
                return TerminateGracefully(), collector, None, None, None
                



        """
        unified_fsm = FilesetExtractor().extract(pud_cfg, shared_cfg, collector)
        unified_flm = FilelistExtractor().extract(pud_cfg, shared_cfg, collector)

        base_resolvers = BaseResolversExtractor().extract(pud_cfg, shared_cfg, collector)
        ui_render = UIRenderExtractor().extract(sys_cfg, collector, unified_fsm, unified_flm)
        pud_doms, shared_doms = DomainsExtractor(collector, unified_fsm, base_resolvers, unified_flm).extract(configs)

        button_map = RtcAssembler().assemble(
            sys_cfg=sys_cfg,
            shared_doms=shared_doms,
            pud_doms=pud_doms,
            collector=collector,
        )
        pud_multidoc_assets = pud_fileset_assets = []
        if pud_state is not PudAssets.States.EMPTY:
            pud_multidoc_assets =self.files.get_dir_manifest(PathTokens.PUD, [".clanker"]) 
            pud_fileset_assets = self.files.get_dir_manifest(PathTokens.PUD, ["content", ".clanker", "README.md"]) # move reademe and .clanker to call above?
            
        shared_multidoc_assets = self.files.get_dir_manifest(PathTokens.SHARED, ["content/a_lib"])
        FilelistValidator().validate(pud_multidoc_assets, pud_doms, shared_multidoc_assets, shared_doms, collector)

        
        shared_fileset_assets = self.files.get_dir_manifest(PathTokens.SHARED, ["content/a_lib"])

        FilesetValidator().validate(pud_fileset_assets, pud_doms, shared_fileset_assets, shared_doms, collector)

        has_soft = bool(collector.get_complaints())
        if repo_state == "co-po":
            action_res = OfferBootstrapWithComplaints() if has_soft else DoBootstrap()
        elif repo_state == "co-pe":
            action_res = OfferClankerizeWithComplaints() if has_soft else OfferClankerize()
        else:
            action_res = TerminateGracefully()

        return action_res, collector, button_map, ui_render, base_resolvers
        """

    def initialize_workspace(self) -> None:
        if self.files.is_cwd_script_dir():
            raise CorruptClanker("Clanker repository initialized is beyond scope of app.")

        try:
            for path in RepoContract.get_all_target_paths():
                self.files.assert_absent(path)
        except AssetExists as ex:
            raise WorkspaceAlreadyInitialized from ex

        for dir_path in RepoContract.DIRS_TO_CREATE:
            self.files.create_dir(dir_path)

        for from_path, to_path in RepoContract.MAPPINGS:
            self.files.copy_file(from_path=from_path, to_path=to_path)