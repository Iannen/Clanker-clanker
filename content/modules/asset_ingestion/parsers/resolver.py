from stdlib import Any, dataclass
from core import (
    MultiDocResolver,
    KBStateResolver,
    RepoContentResolver,
    ManifestResolver,
    Resolver,
    FileSet,
    ConfigAssembly,
)
from ...asset_ingestion import (
    ErrorCollector,
    ValueExtractor,
    FilesetParser,
    FilelistParser,
    #NamedMap,
)

@dataclass
class ResolverParser(ValueExtractor):
    data: dict[str, Any]
    collector: ErrorCollector
    fileset_map: NamedMap
    filelist_map: NamedMap

    def parse(self) -> Resolver | None:
        res_type = self.req_str(self.data, ["type"])
        anchor = self.req_str(self.data, ["id"])

        if res_type == "multi-document-retrieval":
            return self._md_res(anchor)            
        if res_type == "repo_content":
            return self._repo_content(anchor)
        if res_type == "repo-manifest":
            return self._repo_manifest(anchor)
        if res_type in ("kb_info", "kb_state"):
            return KBStateResolver(anchor=anchor)
        raise ConfigAssembly(f"Unsupported resolver type: '{res_type}'")

    def _md_res(self, anchor:str) -> MultiDocResolver | None:
        try: data = self.opt_list(self.data, ["files"], None)
        except ConfigAssembly: data = None
        try: filelist_name = self.opt_str(self.data, ["files"], None)
        except ConfigAssembly: filelist_name = None
        
        
        if filelist_name is not None: filelist_obj = self.filelist_map.get(filelist_name)
        elif data is not None: filelist_obj = FilelistParser(data, self.collector).parse()
        else: raise Exception("bugg")
        return MultiDocResolver(anchor=anchor, files=filelist_obj)

    def _repo_content(self, anchor) -> RepoContentResolver | None:
        fileset_key = self.opt_str(self.data, ["fileset"], [])
        if fileset_key: return RepoContentResolver(anchor=anchor,fileset=self.fileset_map.get(fileset_key))
        fileset_val = {
            "includes": self.req_list(self.data, ["includes"]),
            "excludes": self.opt_list(self.data, ["excludes"], default=[]),
        }
        fileset_obj = FilesetParser(fileset_val, self.collector).parse()

        return RepoContentResolver(anchor=anchor, fileset=fileset_obj)

    def _repo_manifest(self, anchor) -> ManifestResolver | None:
        if "pud_fileset" not in self.data and "shared_fileset" not in self.data:
            raise ConfigAssembly(
                f"Manifest resolver '{anchor}' must specify at least 'pud_fileset' or 'shared_fileset'"
            )

        pud_val = self.opt_str_or_dict(self.data, ["pud_fileset"], default={})
        if isinstance(pud_val, str): pud_fileset_obj = self.fileset_map.get(pud_val)
        else: pud_fileset_obj = FilesetParser(pud_val, self.collector).parse() if pud_val else FileSet(includes=[], excludes=[])
        shared_val = self.opt_str_or_dict(self.data, ["shared_fileset"], default={})
        if isinstance(shared_val, str): shared_fileset_obj = self.fileset_map.get(shared_val)
        else: shared_fileset_obj = FilesetParser(shared_val, self.collector).parse() if shared_val else None

        return ManifestResolver(
            anchor=anchor,
            pud_fileset=pud_fileset_obj,
            shared_fileset=shared_fileset_obj,
        )

