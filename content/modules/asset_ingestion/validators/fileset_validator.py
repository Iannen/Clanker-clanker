from core import Domain, ManifestResolver, RepoContentResolver, AssetPack, Config, Prompt, Fileset, Resolver
from stdlib import dataclass
from ...asset_ingestion import ErrorCollector, Numap

@dataclass
class FilesetValidator2:
    ec: ErrorCollector
    numap: Numap
    clank_cfg: Config
    clank_doc_assets: AssetPack
    pud_cfg: Config
    pud_doc_assets: AssetPack
    pud_content_assets: AssetPack

    def _reqs_from_fileset(self, cls: type[NewReq], dom: Domain, fileset: Fileset, prompt: Prompt | None = None) -> list[NewReq]:
        reqs = [cls(dom, fileset, s, fileset.includes, prompt) for s in fileset.includes]
        if fileset.excludes:
            reqs.extend(cls(dom, fileset, s, fileset.excludes, prompt) for s in fileset.excludes)
        return reqs

    def _reqs_from_resolvers(self, resolvers: list[Resolver], dom: Domain, prompt: Prompt | None = None) -> list[NewReq]:
        reqs = []
        for res in resolvers:
            if isinstance(res, ManifestResolver):
                reqs.extend(self._reqs_from_fileset(FromPud, dom, res.pud_fileset, prompt))
                reqs.extend(self._reqs_from_fileset(FromShared, dom, res.shared_fileset, prompt))
            elif isinstance(res, RepoContentResolver):
                reqs.extend(self._reqs_from_fileset(FromPud, dom, res.fileset, prompt))
        return reqs

    def _get_reqs(self, doms: list[Domain]) -> list[NewReq]:
        reqs: list[NewReq] = []
        for dom in doms:
            reqs.extend(self._reqs_from_resolvers(dom.resolvers, dom))
            for prompt in dom.prompts:
                reqs.extend(self._reqs_from_resolvers(prompt.render.resolvers, dom, prompt))
        return reqs

    def validate(self):
        doms = self.numap.get_entities(Domain)
        reqs = self._get_reqs(doms)
        for req in reqs:
            match req:
                case FromPud():
                    if self.pud_content_assets:
                        if not any(p.startswith(req.subject) for p in self.pud_content_assets.paths):
                            self._remove_subject(req, "pud content assetpack")
                case FromShared():
                    if self.clank_doc_assets:
                        if not any(p.startswith(req.subject) for p in self.clank_doc_assets.paths):
                            self._remove_subject(req, "shared assetpack")

    def _remove_subject(self, req: NewReq, assetpack_name: str):
        self.ec.add_complaint(f"subject removed: '{req.subject}' not found in {assetpack_name}")
        req.target_container.remove(req.subject)

@dataclass
class NewReq:
    dom: Domain
    fileset: Fileset
    subject: str
    target_container: list[str]
    prompt: Prompt | None = None

@dataclass
class FromPud(NewReq): pass

@dataclass
class FromShared(NewReq): pass