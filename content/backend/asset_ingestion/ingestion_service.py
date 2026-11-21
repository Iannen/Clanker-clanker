
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

    def get_runtime_config(self) -> d.BootResult:
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
        shared_doms, pud_doms = assembler.assemble(pud_result)

        if ec.has_crits():
            return d.BootResult(type=d.BootResultType.TERMINATE, shared_domains=[], pud_domains=[], report=ec)
        if pud_result is ClassificationResult.ALL_PRESENT:
            return d.BootResult(type=d.BootResultType.START, shared_domains=shared_doms, pud_domains=pud_doms, report=ec)
        if pud_result is ClassificationResult.NONE_PRESENT:
            return d.BootResult(type=d.BootResultType.CLANKERIZE, shared_domains=[], pud_domains=[], report=ec)

    def initialize_workspace(self) -> d.BootResult:
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
                expanded=list(parsed.expanded),
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
                expanded=list(parsed.expanded),
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
            expanded=list(parsed.expanded),
        )

    def deserialize_domain_prompt(self, data: dict) -> tuple[e.Domain, e.Prompt]:
        if not isinstance(data, dict):
            raise ValueError("Expected a dict")
        if "domain" not in data:
            raise ValueError("Missing 'domain' key")
        if "prompt" not in data:
            raise ValueError("Missing 'prompt' key")

        domain = self._build_domain(data["domain"])
        prompt = self._build_prompt(data["prompt"])
        return domain, prompt

    def _build_domain(self, data: dict) -> e.Domain:
        if not isinstance(data, dict):
            raise ValueError("domain must be a dict")
        name = data.get("name")
        if not name:
            raise ValueError("domain missing 'name'")
        prompts = [self._build_prompt(p) for p in data.get("prompts", [])]
        resolvers = [self._build_resolver(r) for r in data.get("resolvers", [])]
        return e.Domain(name=name, prompts=prompts, resolvers=resolvers)

    def _build_prompt(self, data: dict) -> e.Prompt:
        if not isinstance(data, dict):
            raise ValueError("prompt must be a dict")
        name = data.get("name")
        if not name:
            raise ValueError("prompt missing 'name'")
        render_data = data.get("render")
        if not isinstance(render_data, dict):
            raise ValueError("prompt missing 'render' dict")
        render = self._build_render(render_data)

        expanded_paths = data.get("expanded_paths", [])
        if not isinstance(expanded_paths, list) or not all(
            isinstance(path, str) for path in expanded_paths
        ):
            raise ValueError("prompt 'expanded_paths' must be a list of strings")

        return e.Prompt(
            name=name,
            render=render,
            expanded_paths=expanded_paths,
        )

    def _build_render(self, data: dict) -> e.Render:
        resolvers = [self._build_resolver(r) for r in data.get("resolvers", [])]
        template = data.get("template", "prompt_template")
        inherit_base = data.get("inherit_base", True)
        inherit_domain = data.get("inherit_domain", True)
        return e.Render(resolvers=resolvers, template=template, inherit_base=inherit_base, inherit_domain=inherit_domain)

    def _build_resolver(self, data: dict) -> e.Resolver:
        if not isinstance(data, dict):
            raise ValueError("resolver must be a dict")
        anchor = data.get("anchor")
        if not anchor:
            raise ValueError("resolver missing 'anchor'")

        if "files" in data:
            files = self._build_filelist(data["files"])
            return e.MultiDocResolver(anchor=anchor, files=files)
        elif "content_fileset" in data or "meta_fileset" in data:
            content_fileset = self._build_fileset(data["content_fileset"]) if data.get("content_fileset") else None
            meta_fileset = self._build_fileset(data["meta_fileset"]) if data.get("meta_fileset") else None
            return e.RepoContentResolver(anchor=anchor, content_fileset=content_fileset, meta_fileset=meta_fileset)
        else:
            raise ValueError(f"Cannot determine resolver type from keys: {list(data.keys())}")

    def _build_filelist(self, data: dict) -> e.Filelist:
        if not isinstance(data, dict):
            raise ValueError("filelist must be a dict")
        name = data.get("name")
        files = [self._build_file(f) for f in data.get("files", [])]
        return e.Filelist(name=name, files=files)

    def _build_file(self, data: dict) -> e.File:
        if not isinstance(data, dict):
            raise ValueError("file must be a dict")
        name = data.get("name")
        if not name:
            raise ValueError("file missing 'name'")
        truncation_spec = None
        if data.get("truncation_spec"):
            ts_data = data["truncation_spec"]
            truncation_spec = e.TruncationSpec(
                tail_lines=ts_data.get("tail_lines"),
                from_line=ts_data.get("from_line"),
                up_to=ts_data.get("up_to"),
            )
        path = data.get("path", "")
        return e.File(name=name, truncation_spec=truncation_spec, path=path)

    def _build_fileset(self, data: dict) -> e.Fileset:
        if not isinstance(data, dict):
            raise ValueError("fileset must be a dict")
        name = data.get("name")
        includes = [self._build_fileset_item(i) for i in data.get("includes", [])]
        excludes = [self._build_fileset_item(i) for i in data.get("excludes", [])] if data.get("excludes") else None
        return e.Fileset(name=name, includes=includes, excludes=excludes)

    def _build_fileset_item(self, data: dict) -> e.FilesetItem:
        if not isinstance(data, dict):
            raise ValueError("fileset_item must be a dict")
        value = data.get("value")
        if value is None:
            raise ValueError("fileset_item missing 'value'")
        return e.FilesetItem(value=value)

    @staticmethod
    def _prefix_path(path: str) -> str:
        if path.startswith(e.PathTokens.PUD) or path.startswith(e.PathTokens.SHARED):
            return path
        return f"{e.PathTokens.PUD}/{path}"
