from stdlib import dataclass
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
    NamedMap,
)

@dataclass
class ResolverParser(ValueExtractor):
    collector: ErrorCollector
    entity_cls = Resolver

    def parse(self, name, data, fileset_map: NamedMap, filelist_map: NamedMap) -> Resolver | None:
        res_type = self.req_str(data, ["type"])
        anchor = self.req_str(data, ["id"])

        if res_type == "multi-document-retrieval":
            return self._md_res(anchor, data, filelist_map)            
        if res_type == "repo_content":
            return self._repo_content(anchor, data, fileset_map)
        if res_type == "repo-manifest":
            return self._repo_manifest(anchor, data, fileset_map)
        if res_type in ("kb_info", "kb_state"):
            return KBStateResolver(anchor)
        raise ConfigAssembly(f"Unsupported resolver type: '{res_type}'")

    def _md_res(self, anchor:str, data, filelist_map) -> MultiDocResolver | None:
        try: dict = self.opt_list(data, ["files"], None)
        except ConfigAssembly: dict = None
        try: filelist_name = self.opt_str(data, ["files"], None)
        except ConfigAssembly: filelist_name = None
        
        
        if filelist_name is not None: filelist_obj = filelist_map.get(filelist_name)
        elif dict is not None: filelist_obj = FilelistParser(self.collector).parse("", dict)
        else: raise Exception("bugg")
        return MultiDocResolver(anchor=anchor, files=filelist_obj)

    def _repo_content(self, anchor, data, fileset_map) -> RepoContentResolver | None:
        fileset_key = self.opt_str(data, ["fileset"], [])
        if fileset_key: return RepoContentResolver(anchor=anchor,fileset=fileset_map.get(fileset_key))
        fileset_val = {
            "includes": self.req_list(data, ["includes"]),
            "excludes": self.opt_list(data, ["excludes"], default=[]),
        }
        fileset_obj = FilesetParser(self.collector).parse("",fileset_val)

        return RepoContentResolver(anchor=anchor, fileset=fileset_obj)

    def _repo_manifest(self, anchor, data, fileset_map) -> ManifestResolver | None:
        if "pud_fileset" not in data and "shared_fileset" not in data:
            raise ConfigAssembly(
                f"Manifest resolver '{anchor}' must specify at least 'pud_fileset' or 'shared_fileset'"
            )

        pud_val = self.opt_str_or_dict(data, ["pud_fileset"], default={})
        if isinstance(pud_val, str): pud_fileset_obj = fileset_map.get(pud_val)
        else: pud_fileset_obj = FilesetParser(pud_val, self.collector).parse() if pud_val else FileSet(includes=[], excludes=[])
        shared_val = self.opt_str_or_dict(data, ["shared_fileset"], default={})
        if isinstance(shared_val, str): shared_fileset_obj = fileset_map.get(shared_val)
        else: shared_fileset_obj = FilesetParser(shared_val, self.collector).parse() if shared_val else None

        return ManifestResolver(
            anchor=anchor,
            pud_fileset=pud_fileset_obj,
            shared_fileset=shared_fileset_obj,
        )

