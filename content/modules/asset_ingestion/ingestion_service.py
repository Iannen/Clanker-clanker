from stdlib import dataclass, StrEnum
from core import (
    CorruptClanker,
    ClankerAssets,
    PudAssets,
    PathTokens,
    RepoContract,
    Config,
    AssetPack,
    Filereq,
)
from core.engine_deps import IngestionService, NoSuchFile, DiskPort, ConfigParseError, ConfigParserPort, StartResult, ClankerizeResult, TerminateResult

from . import (
    ErrorCollector,
    Malformed,
    Missing,
    ItemClassifier,
    Assembler,
    ClassificationResult
)


@dataclass(slots=True)
class IngestionServiceImpl(IngestionService):
    files: DiskPort
    cfg_ingestor: ConfigParserPort

    def _get_asset_pack(self, token: str, roots) -> AssetPack | Missing:
        try: return AssetPack(token, "", self.files.get_dir_manifest(token, roots), {})
        except NoSuchFile: return Missing(token, roots)

    def _get_config(self, config: StrEnum) -> Config | Missing | Malformed:
        try:
            raw_content = self.files.get_file_contents(config.value)
            return Config(config.name, config.value, self.cfg_ingestor.get_as_dict(raw_content))
        except NoSuchFile: return Missing(config.name, config.value)
        except ConfigParseError as ex: return Malformed(config.name, config.value, str(ex))

    def _get_file_req(self, filereq: StrEnum) -> Filereq | Missing:
        try: return Filereq(filereq.name, filereq.value, self.files.get_file_contents(filereq.value))
        except IsADirectoryError: return Filereq(filereq.name, filereq.value, "") 
        except NoSuchFile: return Missing(filereq.name, filereq.value) 

    def get_runtime_config(self):
        ec = ErrorCollector()
        clank_classifier = ItemClassifier(ec)
        pud_classifier = ItemClassifier(ec)

        for req in [*ClankerAssets.templates, *ClankerAssets.layouts]: clank_classifier.classify(self._get_file_req(req))
        for req in [*PudAssets.Directories, *PudAssets.Files, *PudAssets.Documentation]: pud_classifier.classify(self._get_file_req(req))

        assembler = Assembler(
            ec, 
            clank_classifier.classify(self._get_config(ClankerAssets.Configs.shared_cfg)),
            clank_classifier.classify(self._get_config(ClankerAssets.Configs.sys_cfg)),
            clank_classifier.classify(self._get_asset_pack(PathTokens.SHARED, ["content/a_lib"])),
            pud_classifier.classify(self._get_config(PudAssets.Configs.configuration_file)), 
            pud_classifier.classify(self._get_asset_pack(PathTokens.PUD, [".clanker"])), 
            pud_classifier.classify(self._get_asset_pack(PathTokens.PUD, ["content", "README.md"])), 
        )
        clank_classifier.complain() 
        pud_result = pud_classifier.evaluate()
        if pud_result is ClassificationResult.MIXED: pud_classifier.complain() 
        ui_render, kb = assembler.assemble(pud_result)

        
        if ec.has_crits(): return TerminateResult(ec) 
        if pud_result is ClassificationResult.ALL_PRESENT: return StartResult(ec, kb, ui_render) 
        if pud_result is ClassificationResult.NONE_PRESENT: return ClankerizeResult(ec)
        
    def initialize_workspace(self):
        if self.files.is_cwd_script_dir():
            raise CorruptClanker("Clanker repository initialized is beyond scope of app.")
        for dir_path in RepoContract.DIRS_TO_CREATE:
            self.files.create_dir(dir_path)

        for from_path, to_path in RepoContract.MAPPINGS:
            self.files.copy_file(from_path=from_path, to_path=to_path)
        return self.get_runtime_config()
