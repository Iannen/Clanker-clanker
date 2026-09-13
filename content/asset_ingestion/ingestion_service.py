from app.models import BasePathTokens, CfgFragments, DocPaths, NoConfig, ConfigAssembly, CorruptClanker, Config, RuntimeConfig
from app.deps.ingestion import IngestionService
from asset_ingestion.commons.error_collector import ErrorCollector

from asset_ingestion.workers.domain_extractor import DomainExtractor
from asset_ingestion.workers.fileset_extractor import FilesetExtractor
from asset_ingestion.workers.rtc_assembler import RtcAssembler
from asset_ingestion.workers.ui_render_extractor import UIRenderExtractor

class IngestionServiceImpl(IngestionService):
    def __init__(
        self,
        files: FileBridgePort,
        cfg_ingestor: ConfigIngestorPort,
    ) -> None:
        self.files = files
        self.cfg_ingestor = cfg_ingestor

    def get_runtime_config(self) -> tuple[Report, RuntimeConfig]:
        try:
            pud_cfg = self._get_validated_cfg_fragment(BasePathTokens.PUD + CfgFragments.PUD_CFG)
        except FileNotFoundError:
            raise NoConfig
        collector = ErrorCollector() #Futurenote: if FNFE -> complain critically to user
        try:
            sys_cfg = self._get_validated_cfg_fragment(BasePathTokens.SHARED + CfgFragments.SYSTEM_CFG)
            shared_cfg = self._get_validated_cfg_fragment(BasePathTokens.SHARED + CfgFragments.SHARED_CFG)
        except FileNotFoundError as ex:
            raise ConfigAssembly(f"Missing configuration fragment: {ex}") from ex

        shared_fsm = FilesetExtractor(shared_cfg, collector).extract()
        pud_fsm = FilesetExtractor(pud_cfg, collector).extract()
        unified_fsm = shared_fsm.merge(pud_fsm)

        ui_render = UIRenderExtractor(sys_cfg, collector).extract()

        shared_doms = DomainExtractor(shared_cfg, collector, unified_fsm).extract()
        pud_doms = DomainExtractor(pud_cfg, collector, unified_fsm).extract()

        assembler = RtcAssembler(
            sys_cfg=sys_cfg,
            shared_doms=shared_doms,
            pud_doms=pud_doms,
            shared_cfg=shared_cfg,
            collector=collector,
            fileset_map=unified_fsm,
        )
        base_resolvers, keyboard = assembler.assemble()

        return collector, RuntimeConfig(
            keyboard=keyboard,
            ui_render=ui_render,
            base_resolvers=base_resolvers,
        )

    def get_runtime_config_old(self) -> tuple[Report, RuntimeConfig]:
        try:
            pud_cfg = self._get_validated_cfg_fragment(BasePathTokens.PUD + CfgFragments.PUD_CFG)
        except FileNotFoundError:
            raise NoConfig

        try:
            sys_cfg = self._get_validated_cfg_fragment(BasePathTokens.SHARED + CfgFragments.SYSTEM_CFG)
            shared_cfg = self._get_validated_cfg_fragment(BasePathTokens.SHARED + CfgFragments.SHARED_CFG)
        except FileNotFoundError as ex:
            raise ConfigAssembly(f"Missing configuration fragment: {ex}") from ex

        return self.assembler.assemble(sys_cfg, pud_cfg, shared_cfg)

    def initialize_workspace(self) -> None:
        if self.files.is_cwd_script_dir():
            raise CorruptClanker("Clanker repository initialized is beyond scope of app.")

        try:
            default_config_data = self._get_validated_cfg_fragment(BasePathTokens.SHARED + CfgFragments.TEMPLATE_CFG)
        except FileNotFoundError as ex:
            raise ConfigAssembly(f"Missing configuration template: {ex}") from ex

        self.files.write_yaml(BasePathTokens.PUD + Config.DEFAULT_REL_PATH, default_config_data)

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