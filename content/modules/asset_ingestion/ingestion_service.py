from stdlib import dataclass, StrEnum
from core import (
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
    FilelistExtractor,
    NewFilelistExtractor,
    FilesetExtractor,
    NewFilesetExtractor,
    DomainExtractor,
    NewDomainExtractor,
    BaseResolverExtractor,
    NewBaseResolverExtractor,
    UIRenderExtractor,
    NewUIRenderExtractor,
    RtcAssembler,
    NewRtcAssembler,
    FilelistValidator,
    FilelistValidatorNew,
    FilelistValidatorNew2,
    FilesetValidator,
    FilesetValidatorNew,
    CollisionDetector,
    NewCollisionDetector,
    Config,
    AssetPack
)
class BootAction(StrEnum):
    START = "ok"
    CLANKERIZE = "empty"
    NONE = "invalid"

@dataclass
class ClankerCtx:
    collector: ErrorCollector
    sys_cfg: Config
    shared_cfg: Config
    doc_assets: AssetPack
    file_reqs: tuple[list[StrEnum], list[StrEnum]]

    def _determine_action(self):
        if self.sys_cfg.issue: self.collector.add_critical_complaint(self.sys_cfg.issue)
        if self.shared_cfg.issue: self.collector.add_critical_complaint(self.shared_cfg.issue)
        if self.doc_assets.issue: self.collector.add_critical_complaint(self.doc_assets.issue)
        missing, _ = self.file_reqs 
        for absentee in missing:
            self.collector.add_critical_complaint(f"'{absentee.name}' not found at '{absentee.value}'")
        self.action = BootAction.START if (not missing and not self.sys_cfg.data is None and not self.shared_cfg.data is None) else BootAction.NONE

    def process(self):
        self._determine_action()
        self.ui_render = NewUIRenderExtractor(self.collector).extract(self.sys_cfg) if self.sys_cfg.data else None
        self.filelist = NewFilelistExtractor(self.collector).extract(self.shared_cfg) if self.shared_cfg.data else None
        self.fileset = NewFilesetExtractor(self.collector).extract(self.shared_cfg) if self.shared_cfg.data else None
        self.doms = NewDomainExtractor(self.collector, self.fileset, self.filelist).extract(self.shared_cfg) if self.shared_cfg.data else None
        self.base_res = NewBaseResolverExtractor(self.collector, self.fileset, self.filelist).extract(self.shared_cfg) if self.shared_cfg.data else None
        if self.doc_assets.paths: NewCollisionDetector(self.collector).detect(self.doc_assets) 

@dataclass
class PudCtx:
    collector: ErrorCollector
    pud_cfg: Config
    doc_assets: AssetPack
    content_assets: AssetPack
    file_reqs: tuple[list[StrEnum], list[StrEnum]]

    def _determine_action(self):
        missing, present = self.file_reqs
        if not missing and self.pud_cfg.data:
            self.action = BootAction.START
        elif not present and self.pud_cfg.data is None:
            self.action = BootAction.CLANKERIZE
        else:
            if self.pud_cfg.issue: self.collector.add_critical_complaint(self.pud_cfg.issue)
            if self.doc_assets.issue: self.collector.add_critical_complaint(self.doc_assets.issue)
            if self.content_assets.issue: self.collector.add_critical_complaint(self.content_assets.issue)
            for absentee in missing:
                self.collector.add_critical_complaint(f"'{absentee.name}' not found at '{absentee.value}'")
            self.action = BootAction.NONE

    def process(self):
        self._determine_action()
        self.filelist = NewFilelistExtractor(self.collector).extract(self.pud_cfg) if self.pud_cfg.data else None
        self.fileset = NewFilesetExtractor(self.collector).extract(self.pud_cfg) if self.pud_cfg.data else None
        if self.doc_assets.paths: NewCollisionDetector(self.collector).detect(self.doc_assets)

class IngestionServiceImpl(IngestionService):
    def __init__(
        self,
        files: DiskPort,
        cfg_ingestor: ConfigParserPort,
    ) -> None:
        self.files = files
        self.cfg_ingestor = cfg_ingestor

    def _phase_1_ctx_acquisition(self) -> tuple[ClankerCtx, PudCtx]:
        clank_collector = ErrorCollector()       
        clank_ctx = ClankerCtx(
            collector = clank_collector,
            sys_cfg = self._get_config(ClankerAssets.Configs.sys_cfg),
            shared_cfg = self._get_config(ClankerAssets.Configs.shared_cfg),
            doc_assets = self._get_asset_pack(PathTokens.SHARED, ["content/a_lib"]),
            file_reqs = self._get_file_reqs([*ClankerAssets.Templates, *ClankerAssets.Layouts])
        )
        pud_collector = ErrorCollector()
        pud_ctx = PudCtx(
            collector = pud_collector,
            pud_cfg = self._get_config(PudAssets.Configs.PUD),
            doc_assets = self._get_asset_pack(PathTokens.PUD, [".clanker"]),
            content_assets = self._get_asset_pack(PathTokens.PUD, ["content", "README.md"]),
            file_reqs = self._get_file_reqs([*PudAssets.Directories, *PudAssets.Files, *PudAssets.Documentation])
        )
        clank_ctx.process()
        pud_ctx.process()
        return clank_ctx, pud_ctx

    def _get_asset_pack(self,token:str, roots) -> AssetPack:
        try:
            return AssetPack(token, roots, self.files.get_dir_manifest(token, roots)) 
        except NoSuchFile:
            # perhaps for this one a simple data | None is fine. 
            return AssetPack(token, roots, None, f"Something missing in '{token}': {roots}") 

    def _get_config(self, config: StrEnum) -> Config:
        try:
            raw_content = self.files.get_file_contents(config.value)
            return Config(config.name, config.value, self.cfg_ingestor.get_as_dict(raw_content))
        except NoSuchFile:
            return Config(config.name, config.value, None, f"'{config.name}' missing. Expected path: {config.value}")
        except ConfigParseError: # here we can get the yaml complaint from ruamel, in the future.
            return Config(config.name, config.value, None, f"'{config.name}' malformed. Path: {config.value}")
    
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

    def new_method(self): # the new public member
        clank_ctx, pud_ctx = self._phase_1_ctx_acquisition()
        merged_collector = ErrorCollector()
        merged_collector.set_complaints(clank_ctx.collector.get_complaints() + pud_ctx.collector.get_complaints())
        merged_collector.set_critical_complaints(clank_ctx.collector.get_critical_complaints() + pud_ctx.collector.get_critical_complaints())
        match (clank_ctx.action, pud_ctx.action, merged_collector.has_crits()):
            case (BootAction.START, BootAction.START, False):

                unified_fsm = clank_ctx.fileset.merge(pud_ctx.fileset)
                unified_flm = clank_ctx.filelist.merge(pud_ctx.filelist)
                pud_doms = NewDomainExtractor(merged_collector, unified_fsm, unified_flm).extract(pud_ctx.pud_cfg)

                for dom in pud_doms+clank_ctx.doms:
                    dom.resolvers = dom.resolvers + clank_ctx.base_res
                button_map = NewRtcAssembler().assemble(
                    sys_cfg=clank_ctx.sys_cfg,
                    shared_doms=clank_ctx.doms,
                    pud_doms=pud_doms,
                    collector=merged_collector,
                )
                (FilelistValidatorNew2(pud_ctx.doc_assets, clank_ctx.doc_assets)
                .validate(pud_ctx.pud_cfg, pud_doms, pud_ctx.collector)
                .validate(clank_ctx.shared_cfg, clank_ctx.doms, clank_ctx.collector))
                """
                (FilelistValidatorNew(pud_ctx.content_assets, clank_ctx.doc_assets)
                .validate(pud_ctx.pud_cfg, pud_doms, pud_ctx.collector)
                .validate(clank_ctx.shared_cfg, clank_ctx.doms, clank_ctx.collector))
                """
                has_soft = bool(merged_collector.get_complaints())
                action_res = OfferBootstrapWithComplaints() if has_soft else DoBootstrap()
                return action_res, merged_collector, button_map, clank_ctx.ui_render, clank_ctx.base_res

            case (BootAction.START, BootAction.CLANKERIZE, False):
                has_soft = bool(merged_collector.get_complaints())
                action_res = OfferClankerizeWithComplaints() if has_soft else OfferClankerize()
                return action_res, merged_collector, None, None, None

            case (_, _, True):
                return TerminateGracefully(), merged_collector, None, None, None
        pass
    # old marker
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
        # entity retrieval. parsers complain if dicts malformed
        ui_render = UIRenderExtractor(collector).extract(sys_cfg)
        filelist = FilelistExtractor(collector).extract(cfg)
        fileset = FilesetExtractor(collector).extract(cfg)
        # entity retrieval. complains if dict malformed or named members cannot be satisfied from maps provided
        doms = DomainExtractor(collector, fileset, filelist).extract(cfg)
        base_res = BaseResolverExtractor(collector, fileset, filelist).extract(cfg)
        # collisions of md assets 
        CollisionDetector(collector).detect(self.files.get_dir_manifest(PathTokens.SHARED, ["content/a_lib"]))
        # i think that is all we can do with clanker configs alone. i must add presence of asset lib to critical check list
        return filelist, fileset, doms, base_res, ui_render
    def _validate_pud(self, collector, cfg):
        # what can we do here? we can get the no-prereq entities, validating their shape.
        # we dont have an ui render to get, so...
        filelist = FilelistExtractor(collector).extract(cfg)
        fileset = FilesetExtractor(collector).extract(cfg)
        # we cannot get the domains or base_res, because we need unified prereqs to replace named prereqs in dicts
        #but we can check for collisions of file assets
        CollisionDetector(collector).detect(self.files.get_dir_manifest(PathTokens.PUD, [".clanker"]))
        return filelist, fileset

    def get_runtime_config(self) -> tuple[ActionResult, Report, dict[str, Button], Render, list[Resolver]]:
        clank_collector = ErrorCollector()
        pud_collector = ErrorCollector()



        #these 4 lines shall become 1, yielding clanker state, pud state and configs. 
        clanker_state, clank_cfgs = self._resolve_clanker_state(clank_collector)
        pud_state, pud_cfgs = self._resolve_pud_state(clank_collector)
        repo_state = f"{clanker_state}-{pud_state}"
        configs = {**clank_cfgs, **pud_cfgs}

        # or perhaps we receive a typed object containing these in place of 'configs' dict
        sys_cfg = clank_cfgs.get(ClankerAssets.Configs.sys_cfg.name)
        shared_cfg = clank_cfgs.get(ClankerAssets.Configs.shared_cfg.name)
        pud_cfg = pud_cfgs.get(PudAssets.Configs.PUD.name)

        match (clanker_state, pud_state):
            case (ClankerAssets.States.OK, PudAssets.States.OK):
                shared_flm, shared_fsm, shared_doms, base_resolvers, ui_render = self._validate_clanker(clank_collector, shared_cfg, sys_cfg)
                pud_flm, pud_fsm = self._validate_pud(clank_collector, pud_cfg)
                unified_fsm = shared_fsm.merge(pud_fsm)
                unified_flm = shared_flm.merge(pud_flm)
                pud_doms = DomainExtractor(clank_collector, unified_fsm, unified_flm).extract(pud_cfg)

                ## assembly stuff.
                for dom in pud_doms+shared_doms:
                    dom.resolvers = dom.resolvers + base_resolvers
                button_map = RtcAssembler().assemble(
                    sys_cfg=sys_cfg,
                    shared_doms=shared_doms,
                    pud_doms=pud_doms,
                    collector=clank_collector,
                )
                pud_multidoc_assets =self.files.get_dir_manifest(PathTokens.PUD, [".clanker"]) 
                pud_fileset_assets = self.files.get_dir_manifest(PathTokens.PUD, ["content", ".clanker", "README.md"])
                shared_multidoc_assets = self.files.get_dir_manifest(PathTokens.SHARED, ["content/a_lib"])
                shared_manifest_assets = self.files.get_dir_manifest(PathTokens.SHARED, ["content/a_lib"])

                FilelistValidator().validate("pud_cfg", pud_doms, pud_multidoc_assets, shared_multidoc_assets, clank_collector) 
                FilelistValidator().validate("shared_cfg", shared_doms, pud_multidoc_assets, shared_multidoc_assets, clank_collector) 

                FilesetValidator().validate("pud_cfg", pud_doms, pud_fileset_assets, shared_manifest_assets, clank_collector)
                FilesetValidator().validate("shared_cfg", shared_doms, pud_fileset_assets, shared_manifest_assets, clank_collector)

                has_soft = bool(clank_collector.get_complaints())
                action_res = OfferBootstrapWithComplaints() if has_soft else DoBootstrap()
                return action_res, clank_collector, button_map, ui_render, base_resolvers
            case (ClankerAssets.States.OK, PudAssets.States.EMPTY):
                self._validate_clanker(clank_collector, shared_cfg, sys_cfg)
                has_soft = bool(clank_collector.get_complaints())
                action_res = OfferClankerizeWithComplaints() if has_soft else OfferClankerize()
                return action_res, clank_collector, None, None, None
            case (ClankerAssets.States.OK, PudAssets.States.BAD):
                self._validate_clanker(clank_collector)
                return TerminateGracefully(), clank_collector, None, None, None
            case (ClankerAssets.States.BAD, PudAssets.States.OK):
                self._validate_pud(clank_collector)
                return TerminateGracefully(), clank_collector, None, None, None
            case (ClankerAssets.States.BAD, PudAssets.States.EMPTY):
                return TerminateGracefully(), clank_collector, None, None, None
            case (ClankerAssets.States.BAD, PudAssets.States.BAD):
                return TerminateGracefully(), clank_collector, None, None, None

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