from stdlib import dataclass
from core import Domain, File, MultiDocResolver, PathTokens, AssetPack, Config, SharedDomain, PudDomain, Prompt
from ...asset_ingestion import ErrorCollector, Numap

@dataclass
class FilelistValidator2:
    ec: ErrorCollector
    clank_doc_assets: AssetPack
    clank_cfg: Config
    pud_doc_assets: AssetPack
    pud_cfg: Config
    numap: Numap

    # it turns out that clank must be allowed to source documents from pud, such as north star documents and the like.
    # so I must differentiate library assets from other assets to constrain clank, probably via more entities and that
    def validate_clank(self):
        doms = self.numap.get_entities(SharedDomain)
        reqs: list[Req] = self._get_reqs(doms, self.clank_cfg)
        self.shared_map = {p.rsplit("/", 1)[-1]: f"{PathTokens.SHARED}/{p}" for p in self.clank_doc_assets.paths}
        self.pud_map = {p.rsplit("/", 1)[-1]: f"{PathTokens.SHARED}/{p}" for p in self.pud_doc_assets.paths} if self.pud_doc_assets else {}
        self.combined_map = self.pud_map | self.shared_map

        for req in reqs:
            target_path = self.combined_map.get(req.file.name)
            if target_path:
                req.file.path = target_path
            else:
                self._remove_file(req)

    def validate_pud(self):
        doms = self.numap.get_entities(PudDomain)
        reqs: list[Req] = self._get_reqs(doms, self.pud_cfg)

        for req in reqs:
            target_path = self.combined_map.get(req.file.name)
            if target_path:
                req.file.path = target_path
            else:
                self._remove_file(req)

    def _get_reqs(self, doms: list[Domain], cfg: Config) -> list[tuple[File, str]]:
        reqs: list[Req] = []

        for dom in doms:
            for resolver in dom.resolvers:
                if isinstance(resolver, MultiDocResolver):
                    for file_item in resolver.files.files:
                        reqs.append(Req(cfg, dom, resolver, file_item))

            for prompt in getattr(dom, "prompts", []):
                for resolver in prompt.render.resolvers:
                    if isinstance(resolver, MultiDocResolver):
                        for file_item in resolver.files.files:
                            reqs.append(Req(cfg, dom, resolver, file_item, prompt))
        return reqs

    def _remove_file(self, req: Req):
        with self.ec.path(req.cfg.name):
            complaintstr = f"File '{req.file.name}' removed: unsatisfied by asset pack."
            self.ec.add_complaint(complaintstr)
        req.mdr.files.files = [f for f in req.mdr.files.files if f != req.file]

@dataclass
class Req:
    cfg: Config
    dom: Domain
    mdr: MultiDocResolver
    file: File
    prompt: Prompt | None = None