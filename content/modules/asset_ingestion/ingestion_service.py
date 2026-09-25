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
    DoBootstrap
)
from core.engine_deps import IngestionService, Report, NoSuchFile, AssetExists, DiskPort, ConfigParseError, ConfigParserPort

from . import (
    ErrorCollector,
    FilesetExtractor,
    FilelistExtractor,
    BaseResolversExtractor,
    UIRenderExtractor,
    DomainsExtractor,
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

    def _resolve_clanker_state(self, collector: ErrorCollector) -> tuple[str, dict | None, dict | None]:
        sys_cfg = shared_cfg = None
        clanker_state = "co"

        for fragment_path, name in [
            (ClankerAssets.Configs.SYSTEM, "system_cfg"),
            (ClankerAssets.Configs.SHARED, "shared_cfg"),
        ]:
            try:
                raw_content = self.files.get_file_contents(fragment_path)
                parsed = self.cfg_ingestor.get_as_dict(raw_content)
                if name == "system_cfg":
                    sys_cfg = parsed
                else:
                    shared_cfg = parsed
            except NoSuchFile:
                clanker_state = "cb"
                collector.add_critical_complaint(f"Missing clanker asset: {fragment_path}")
            except ConfigParseError:
                clanker_state = "cb"
                collector.add_critical_complaint(f"Failed to convert clanker config: {fragment_path}")

        for asset_path in (*ClankerAssets.Templates, *ClankerAssets.Layouts):
            try:
                self.files.read_asset(asset_path)
            except NoSuchFile:
                clanker_state = ClankerAssets.States.BAD
                collector.add_critical_complaint(f"Missing clanker asset: {asset_path}")

        return clanker_state, sys_cfg, shared_cfg

    def _resolve_pud_state(self, collector: ErrorCollector) -> tuple[str, dict | None]:
        pud_cfg = None
        pud_assets = [
            *PudAssets.Configs,
            *PudAssets.Directories,
            *PudAssets.Files,
            *PudAssets.Documentation,
        ]

        existing_count = 0
        pud_crit_complaints = []

        for asset_path in pud_assets:
            try:
                if asset_path == PudAssets.Configs.PUD:
                    raw_content = self.files.get_file_contents(asset_path)
                    pud_cfg = self.cfg_ingestor.get_as_dict(raw_content)
                    existing_count += 1
                elif asset_path == PudAssets.Directories.CONTENTS:
                    self.files.get_dir_manifest(PathTokens.PUD, ["content"])
                    existing_count += 1
                else:
                    self.files.get_file_contents(asset_path)
                    existing_count += 1
            except NoSuchFile:
                pud_crit_complaints.append(f"Missing pud asset: {asset_path}")
            except ConfigParseError:
                existing_count += 1
                pud_crit_complaints.append(f"Non-convertible pud config: {asset_path}")

        if existing_count == len(pud_assets) and not pud_crit_complaints:
            return "po", pud_cfg
        elif existing_count == 0:
            return "pe", pud_cfg
        else:
            for complaint in pud_crit_complaints:
                collector.add_critical_complaint(complaint)
            return "pb", pud_cfg

    def get_runtime_config(self) -> tuple[ActionResult, Report, dict[str, Button], Render, list[Resolver]]:
        collector = ErrorCollector()

        ## TODO: put this behind a helper which returns to us.. 
        ## repo_states:str, configs: dict[name, config]
        clanker_state, sys_cfg, shared_cfg = self._resolve_clanker_state(collector)
        pud_state, pud_cfg = self._resolve_pud_state(collector)
        repo_state = f"{clanker_state}-{pud_state}"
        configs = {name: cfg for name, cfg in [("shared", shared_cfg), ("pud", pud_cfg), ("sys_cfg", sys_cfg)]}

        ## make the resolvers accep the configs collection, and deal with the configs perhaps being None
        unified_fsm = FilesetExtractor().extract(pud_cfg, shared_cfg, collector)
        unified_flm = FilelistExtractor().extract(pud_cfg, shared_cfg, collector)

        #this too accept the configs collection -> deal with the configs perhaps being None
        base_resolvers = BaseResolversExtractor().extract(pud_cfg, shared_cfg, collector)
        #this too
        ui_render = UIRenderExtractor().extract(sys_cfg, collector, unified_fsm, unified_flm)
        #this too
        pud_doms, shared_doms = DomainsExtractor().extract(pud_cfg, shared_cfg, collector, unified_fsm, base_resolvers, unified_flm)
        # this too, perhaps a noop if we didnt have all 3 configs
        button_map = RtcAssembler().assemble(
            sys_cfg=sys_cfg,
            shared_doms=shared_doms,
            pud_doms=pud_doms,
            collector=collector,
        )
        # and so on, we try to validate and collect complaints, and just return None if we have to
        pud_multidoc_assets = self.files.get_dir_manifest(PathTokens.PUD, [".clanker"])
        shared_multidoc_assets = self.files.get_dir_manifest(PathTokens.SHARED, ["content/a_lib"])
        FilelistValidator().validate(pud_multidoc_assets, pud_doms, shared_multidoc_assets, shared_doms, collector)

        pud_fileset_assets = self.files.get_dir_manifest(PathTokens.PUD, ["content", ".clanker", "README.md"])
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