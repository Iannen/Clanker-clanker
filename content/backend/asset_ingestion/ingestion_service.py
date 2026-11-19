from backend.stdlib import dataclass, StrEnum
from backend.core import entities as e
from backend.core import engine_deps as d

from . import ErrorCollector, ItemClassifier, Assembler, ClassificationResult
from .ingestion_parser import IngestionParser


@dataclass
class IngestionServiceImpl(d.IngestionService):
    files: d.DiskPort
    cfg_ingestor: d.ConfigParserPort

    def _get_asset_pack(self, token: str, roots: list[str] | None = None) -> e.AssetPack | d.Missing:
        try: return e.AssetPack(token, self.files.get_dir_manifest(token, roots))
        except d.NoSuchFile: return d.Missing(token, roots)

    def _get_config(self, config: StrEnum) -> e.Config | d.Missing | d.Malformed:
        try:
            raw_content = self.files.get_file_contents(config.value)
            return e.Config(config.name, config.value, self.cfg_ingestor.get_as_dict(raw_content))
        except d.NoSuchFile: return d.Missing(config.name, config.value)
        except d.ConfigParseError as ex: return d.Malformed(config.name, config.value, str(ex))

    def _get_file_req(self, filereq: StrEnum) -> e.Filereq | d.Missing:
        try: return e.Filereq(filereq.name, filereq.value, self.files.get_file_contents(filereq.value))
        except IsADirectoryError: return e.Filereq(filereq.name, filereq.value, "")
        except d.NoSuchFile: return d.Missing(filereq.name, filereq.value)

    def get_runtime_config(self) -> tuple[d.StartCmd | d.StartResult | d.ClankerizeResult | d.TerminateResult, d.BootResult | None]:
        ec = ErrorCollector()
        clank_classifier = ItemClassifier(ec)
        pud_classifier = ItemClassifier(ec)

        for req in [*e.ClankerAssets.templates, *e.ClankerAssets.layouts]: clank_classifier.classify(self._get_file_req(req))
        for req in [*e.PudAssets.Directories, *e.PudAssets.Files, *e.PudAssets.Documentation]: pud_classifier.classify(self._get_file_req(req))

        assembler = Assembler(
            ec,
            clank_classifier.classify(self._get_config(e.ClankerAssets.Configs.shared_cfg)),
            clank_classifier.classify(self._get_config(e.ClankerAssets.Configs.sys_cfg)),
            clank_classifier.classify(self._get_asset_pack(e.PathTokens.SHARED, ["content/a_lib"])),
            pud_classifier.classify(self._get_config(e.PudAssets.Configs.configuration_file)),
            pud_classifier.classify(self._get_asset_pack(e.PathTokens.PUD, [".clanker"])),
            pud_classifier.classify(self._get_asset_pack(e.PathTokens.PUD)),
        )
        clank_classifier.complain()
        pud_result = pud_classifier.evaluate()
        if pud_result is ClassificationResult.MIXED: pud_classifier.complain()
        kb, shared_doms, pud_doms = assembler.assemble(pud_result)
        boot = d.BootResult(shared_domains=shared_doms, pud_domains=pud_doms)

        if ec.has_crits(): return d.TerminateResult(ec), None
        if pud_result is ClassificationResult.ALL_PRESENT:
            if not ec.get_all_complaints():
                return d.StartCmd(kb=kb), boot
            return d.StartResult(ec, kb), boot
        if pud_result is ClassificationResult.NONE_PRESENT: return d.ClankerizeResult(ec), None

    def initialize_workspace(self) -> tuple[d.StartCmd | d.StartResult | d.ClankerizeResult | d.TerminateResult, d.BootResult | None]:
        if self.files.is_cwd_script_dir():
            raise e.CorruptClanker("Clanker repository initialized is beyond scope of app.")
        for dir_path in e.RepoContract.DIRS_TO_CREATE:
            self.files.create_dir(dir_path)

        for from_path, to_path in e.RepoContract.MAPPINGS:
            self.files.copy_file(from_path=from_path, to_path=to_path)
        return self.get_runtime_config()

    def apply_file_changes(self, raw_text: str) -> d.IngestApplyResult:
        parsed = IngestionParser().parse(raw_text)

        # Pre-flight: reject on parse errors
        if parsed.errors:
            return d.IngestApplyResult(
                created=[], updated=[], deleted=[],
                missing_paths=[], unexpected_paths=[],
                parse_errors=list(parsed.errors),
            )

        # Pre-flight: create paths must NOT exist
        unexpected_paths: list[str] = []
        for path, _ in parsed.creates:
            tokenized = self._prefix_path(path)
            try:
                self.files.get_file_contents(tokenized)
                unexpected_paths.append(path)
            except d.NoSuchFile:
                pass

        # Pre-flight: update paths must exist
        missing_paths: list[str] = []
        for path, _ in parsed.updates:
            tokenized = self._prefix_path(path)
            try:
                self.files.get_file_contents(tokenized)
            except d.NoSuchFile:
                missing_paths.append(path)

        # Pre-flight: delete paths must exist
        for path in parsed.deletes:
            tokenized = self._prefix_path(path)
            try:
                self.files.get_file_contents(tokenized)
            except d.NoSuchFile:
                missing_paths.append(path)

        if unexpected_paths or missing_paths:
            return d.IngestApplyResult(
                created=[], updated=[], deleted=[],
                missing_paths=missing_paths,
                unexpected_paths=unexpected_paths,
                parse_errors=[],
            )

        # All checks passed – perform disk operations
        created: list[str] = []
        updated: list[str] = []
        deleted: list[str] = []

        for path, content in parsed.creates:
            tokenized = self._prefix_path(path)
            try:
                self.files.write_file(tokenized, content.strip("\n"))
                created.append(path)
            except Exception as ex:
                raise RuntimeError(f"Write failed for {path}: {ex}") from ex

        for path, content in parsed.updates:
            tokenized = self._prefix_path(path)
            try:
                self.files.write_file(tokenized, content.strip("\n"))
                updated.append(path)
            except Exception as ex:
                raise RuntimeError(f"Update failed for {path}: {ex}") from ex

        for path in parsed.deletes:
            tokenized = self._prefix_path(path)
            try:
                self.files.delete_file(tokenized)
                deleted.append(path)
            except Exception as ex:
                raise RuntimeError(f"Delete failed for {path}: {ex}") from ex

        return d.IngestApplyResult(
            created=created, updated=updated, deleted=deleted,
            missing_paths=[], unexpected_paths=[], parse_errors=[],
        )

    @staticmethod
    def _prefix_path(path: str) -> str:
        if path.startswith(e.PathTokens.PUD) or path.startswith(e.PathTokens.SHARED):
            return path
        return f"{e.PathTokens.PUD}/{path}"