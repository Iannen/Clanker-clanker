from app.models import BasePathTokens, CfgFragments, DocPaths, NoConfig, ConfigAssembly, CorruptClanker, Config
from dep_visibility.ingestion import IngestionService
#TODO: make app crash cuz typeannotations not reffd

class IngestionServiceImpl(IngestionService):
    def __init__(
        self,
        files: FileBridgePort,
        cfg_ingestor: ConfigIngestorPort,
        assembler: RtcAssembler,
    ) -> None:
        self.files = files
        self.cfg_ingestor = cfg_ingestor
        self.assembler = assembler

    def _get_validated_cfg_fragment(self, fragment_token_path: str) -> dict:
        raw_content = self.files.get_file_contents(fragment_token_path)
        cfg_dict = self.cfg_ingestor.get_as_dict(raw_content)
        return cfg_dict

    def get_runtime_config(self) -> tuple[Report, RuntimeConfig]:
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