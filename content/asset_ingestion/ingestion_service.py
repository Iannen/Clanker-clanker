from app.deps.ingestion import IngestionService
from app.models import BasePathTokens, CfgFragments, DocPaths, NoConfig, ConfigAssembly, CorruptClanker, Config, RuntimeConfig, KBStateResolver
from asset_ingestion.commons.value_extractor import ValueExtractor
from asset_ingestion.commons.error_collector import ErrorCollector
from asset_ingestion.extractors.domains import DomainsExtractor
from asset_ingestion.extractors.fileset import FilesetExtractor
from asset_ingestion.assemblers.rtc import RtcAssembler
from asset_ingestion.parsers.render import RenderParser
from asset_ingestion.extractors.base_resolver import BaseResolverExtractor

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

        shared_base_res = BaseResolverExtractor(shared_cfg, collector).extract()
        pud_base_res = BaseResolverExtractor(pud_cfg, collector).extract()

        if pud_base_res is not None:
            base_resolvers = [pud_base_res]
        elif shared_base_res is not None:
            base_resolvers = [shared_base_res]
        else:
            collector.add_complaint("Missing required base resolver configuration")
            base_resolvers = []

        with collector.path("ui_render"):
            ui_render_dict = ValueExtractor().req_dict(sys_cfg, ["ui_render"])
            ui_render = RenderParser(ui_render_dict, collector, unified_fsm).extract()
            kb_resolvers = [r for r in ui_render.resolvers if isinstance(r, KBStateResolver)]
            if len(kb_resolvers) != 1:
                collector.add_complaint(
                    f"ui_render must carry exactly one KBStateResolver ('kb_info'), found {len(kb_resolvers)}"
                )

        shared_doms = DomainsExtractor(shared_cfg, collector, unified_fsm).extract()
        pud_doms = DomainsExtractor(pud_cfg, collector, unified_fsm).extract()

        assembler = RtcAssembler(
            sys_cfg=sys_cfg,
            shared_doms=shared_doms,
            pud_doms=pud_doms,
            shared_cfg=shared_cfg,
            collector=collector,
            fileset_map=unified_fsm,
        )
        keyboard = assembler.assemble()

        return collector, RuntimeConfig(
            keyboard=keyboard,
            ui_render=ui_render,
            base_resolvers=base_resolvers,
        )

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