from app.deps.ingestion import IngestionService
from app.entities import KBStateResolver
from app.exceptions import NoConfig, ConfigAssembly, CorruptClanker, WorkspaceAlreadyInitialized
from ports_adapters.ports import PathTokens, NoSuchFile, AssetExists, DiskPort, ConfigParseError, ConfigParserPort
from asset_ingestion.commons.value_extractor import ValueExtractor
from asset_ingestion.commons.error_collector import ErrorCollector
from asset_ingestion.extractors.domains import DomainsExtractor
from asset_ingestion.extractors.fileset import FilesetExtractor
from asset_ingestion.assemblers.rtc import RtcAssembler
from asset_ingestion.parsers.render import RenderParser
from asset_ingestion.extractors.base_resolver import BaseResolversExtractor
from asset_ingestion.extractors.ui_render import UIRenderExtractor
from asset_ingestion.validators.assets import FilesetValidator
from asset_ingestion.validators.file_list import FilelistValidator
from app.constants import CfgFragments, PathTokens, DocPaths, TemplatePaths
from app.presentation import ActionResult

class IngestionServiceImpl(IngestionService):
    def __init__(
        self,
        files: DiskPort,
        cfg_ingestor: ConfigParserPort,
    ) -> None:
        self.files = files
        self.cfg_ingestor = cfg_ingestor

    def get_runtime_config(self) -> tuple[ActionResult, Report, dict[str, Button], Render, list[Resolver]]:
        collector = ErrorCollector() 
        try:
            pud_cfg = self._get_validated_cfg_fragment(CfgFragments.PUD_CFG)
        except NoSuchFile:
            raise NoConfig
        try:
            sys_cfg = self._get_validated_cfg_fragment(CfgFragments.SYSTEM_CFG)
            shared_cfg = self._get_validated_cfg_fragment(CfgFragments.SHARED_CFG)
        except NoSuchFile as ex:
            raise ConfigAssembly(f"Missing configuration fragment: {ex}") from ex

        unified_fsm = FilesetExtractor().extract(pud_cfg, shared_cfg, collector)

        base_resolvers = BaseResolversExtractor().extract(pud_cfg, shared_cfg, collector)

        ui_render = UIRenderExtractor().extract(sys_cfg, collector, unified_fsm)

        pud_doms, shared_doms = DomainsExtractor().extract(pud_cfg, shared_cfg, collector, unified_fsm, base_resolvers)

        button_map = RtcAssembler().assemble(
            sys_cfg=sys_cfg,
            shared_doms=shared_doms,
            pud_doms=pud_doms,
            collector=collector,
        )

        pud_multidoc_assets = self.files.get_files(PathTokens.PUD, [".clanker"])
        shared_multidoc_assets = self.files.get_files(PathTokens.SHARED, ["content/a_lib"])
        FilelistValidator().validate(pud_multidoc_assets, pud_doms, shared_multidoc_assets, shared_doms, collector)
        
        pud_fileset_assets = self.files.get_files(PathTokens.PUD, ["content", ".clanker", "README.md"])
        shared_fileset_assets = self.files.get_files(PathTokens.SHARED, ["content/a_lib"])

        FilesetValidator().validate(pud_fileset_assets, pud_doms, shared_fileset_assets, shared_doms, collector)

        action_res = ActionResult(ActionResult.BOOTSTRAP_SUCCESS)
        return action_res, collector, button_map, ui_render, base_resolvers

    def initialize_workspace(self) -> None:
        if self.files.is_cwd_script_dir():
            raise CorruptClanker("Clanker repository initialized is beyond scope of app.")

        pud_clanker_dir = PathTokens.PUD + "/.clanker"
        target_readme = PathTokens.PUD + "/README.md"

        try:
            self.files.assert_absent(pud_clanker_dir)
            self.files.assert_absent(target_readme)
        except AssetExists as ex:
            raise WorkspaceAlreadyInitialized from ex

        self.files.copy_file(
            from_path=TemplatePaths.CFG_TEMPLATE,
            to_dir=pud_clanker_dir,
            from_ext=DocPaths.TEMPL_EXT,
            to_ext=".yaml",
        )

        self.files.copy_file(
            from_path=TemplatePaths.README_TEMPLATE,
            to_dir=PathTokens.PUD,
            from_ext=DocPaths.TEMPL_EXT,
            to_ext=".md",
        )

        for templ_path in (
            TemplatePaths.ARCH_TEMPLATE,
            TemplatePaths.BACKLOG_TEMPLATE,
            TemplatePaths.NORTH_STAR_TEMPLATE,
            TemplatePaths.PROJECT_HISTORY_TEMPLATE,
        ):
            self.files.copy_file(
                from_path=templ_path,
                to_dir=DocPaths.PUD_DOCS,
                from_ext=DocPaths.TEMPL_EXT,
                to_ext=DocPaths.DOC_EXT,
            )

    def _get_validated_cfg_fragment(self, fragment_token_path: str) -> dict:
        raw_content = self.files.get_file_contents(fragment_token_path)
        try:
            cfg_dict = self.cfg_ingestor.get_as_dict(raw_content)
        except ConfigParseError as ex:
            raise ConfigAssembly() from ex
        return cfg_dict