from app.deps.ingestion import IngestionService
from app.entities import KBStateResolver
from app.exceptions import NoConfig, ConfigAssembly, CorruptClanker
from ports_adapters.ports import NoSuchFile
from asset_ingestion.commons.value_extractor import ValueExtractor
from asset_ingestion.commons.error_collector import ErrorCollector
from asset_ingestion.extractors.domains import DomainsExtractor
from asset_ingestion.extractors.fileset import FilesetExtractor
from asset_ingestion.assemblers.rtc import RtcAssembler
from asset_ingestion.parsers.render import RenderParser
from asset_ingestion.extractors.base_resolver import BaseResolversExtractor
from asset_ingestion.extractors.ui_render import UIRenderExtractor
from asset_ingestion.validators.assets import AssetValidator
from app.constants import CfgFragments, PathTokens, DocPaths

class IngestionServiceImpl(IngestionService):
    def __init__(
        self,
        files: FileBridgePort,
        cfg_ingestor: ConfigIngestorPort,
    ) -> None:
        self.files = files
        self.cfg_ingestor = cfg_ingestor

    def get_runtime_config(self) -> tuple[Report, dict[str, Button], Render, list[Resolver]]:
        try:
            pud_cfg = self._get_validated_cfg_fragment(CfgFragments.PUD_CFG)
        except NoSuchFile:
            raise NoConfig
        collector = ErrorCollector() 
        try:
            sys_cfg = self._get_validated_cfg_fragment(CfgFragments.SYSTEM_CFG)
            shared_cfg = self._get_validated_cfg_fragment(CfgFragments.SHARED_CFG)
        except NoSuchFile as ex:
            #if NoSuchFile -> complain critically to user not raise
            raise ConfigAssembly(f"Missing configuration fragment: {ex}") from ex

        unified_fsm = FilesetExtractor().extract(pud_cfg, shared_cfg, collector)

        base_resolvers = BaseResolversExtractor().extract(pud_cfg, shared_cfg, collector)

        ui_render = UIRenderExtractor().extract(sys_cfg, collector, unified_fsm)

        pud_doms, shared_doms = DomainsExtractor().extract(pud_cfg, shared_cfg, collector, unified_fsm)

        keyboard = RtcAssembler().assemble(
            sys_cfg=sys_cfg,
            shared_doms=shared_doms,
            pud_doms=pud_doms,
            collector=collector,
        )

        pud_filelist = self.files.get_files(PathTokens.PUD, ["."], missing_ok=True)
        shared_filelist = self.files.get_files(PathTokens.SHARED, ["."], missing_ok=True)

        AssetValidator().validate(
            pud_pathlist=pud_filelist,
            shared_pathlist=shared_filelist,
            keyboard=keyboard,
            ui_render=ui_render,
            base_resolvers=base_resolvers,
            collector=collector,
        )

        return collector, keyboard.button_map, ui_render, base_resolvers

    def initialize_workspace(self) -> None:
        if self.files.is_cwd_script_dir():
            raise CorruptClanker("Clanker repository initialized is beyond scope of app.")

        try:
            default_config_data = self._get_validated_cfg_fragment(CfgFragments.TEMPLATE_CFG)
        except NoSuchFile as ex:
            raise ConfigAssembly(f"Missing configuration template: {ex}") from ex

        self.files.write_yaml(CfgFragments.PUD_CFG, default_config_data)

        self.files.write_default_documents(
            doc_templ_dir=DocPaths.SHARED_TEMPLATES,
            pud_doc_dir=DocPaths.PUD_DOCS,
            templ_ext=DocPaths.TEMPL_EXT,
            doc_ext=DocPaths.DOC_EXT
        )

    def _get_validated_cfg_fragment(self, fragment_token_path: str) -> dict:
        raw_content = self.files.get_file_contents(fragment_token_path)
        cfg_dict = self.cfg_ingestor.get_as_dict(raw_content)
        return cfg_dict