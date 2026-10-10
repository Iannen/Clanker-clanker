from stdlib import dataclass
from core import Domain, File, MultiDocResolver, AssetPack, Config, SharedDomain, PudDomain
from ...asset_ingestion import ErrorCollector, Numap, UnsatisfiedFiles

@dataclass
class FilelistValidator2:
    ec: ErrorCollector
    clank_doc_assets: AssetPack
    clank_cfg: Config
    pud_doc_assets: AssetPack
    pud_cfg: Config
    numap: Numap

    def validate(self):
        if not (self.clank_doc_assets and self.clank_cfg and self.pud_doc_assets and self.pud_cfg): return
        self.combined_map = self.pud_doc_assets.resolved_map | self.clank_doc_assets.resolved_map
        self._validate_domain_group(self.clank_cfg, self.numap.get_entities(SharedDomain))
        self._validate_domain_group(self.pud_cfg, self.numap.get_entities(PudDomain))

    def _validate_domain_group(self, cfg: Config, doms: list[Domain]) -> None:
        reqs = self._get_reqs(doms)
        unsatisfied = self._handle_reqs(reqs)
        self._handle_unsatisfied(cfg, unsatisfied)

    def _get_reqs(self, doms: list[Domain]) -> list[Req]:
        reqs: list[Req] = []

        for dom in doms:
            for res in dom.resolvers:
                if isinstance(res, MultiDocResolver):
                    for file_item in res.files.files:
                        reqs.append(Req(res, file_item))

            for prompt in dom.prompts:
                for res in prompt.render.resolvers:
                    if isinstance(res, MultiDocResolver):
                        for file_item in res.files.files:
                            reqs.append(Req(res, file_item))
        return reqs

    def _handle_reqs(self, reqs: list[Req]) -> list[Req]:
        unsatisfied: list[Req] = []
        for req in reqs:
            target_path = self.combined_map.get(req.file.name)
            if target_path:
                req.file.path = target_path
            else:
                unsatisfied.append(req)
        return unsatisfied

    def _handle_unsatisfied(self, cfg: Config, unsatisfied: list[Req]):
        if not unsatisfied: return
        files = [req.file for req in unsatisfied]
        self.ec.accept(UnsatisfiedFiles(cfg, files))
        for req in unsatisfied:
            req.mdr.files.files = [f for f in req.mdr.files.files if f != req.file]

@dataclass
class Req:
    mdr: MultiDocResolver
    file: File