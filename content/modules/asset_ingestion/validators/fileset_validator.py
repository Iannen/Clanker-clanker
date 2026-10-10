from core import Domain, ManifestResolver, RepoContentResolver, Config, Fileset, Resolver
from stdlib import dataclass
from ...asset_ingestion import ErrorCollector, Numap, UnsatisfiedFilesetSubjects, AssetPack

@dataclass
class FilesetValidator2:
    ec: ErrorCollector
    numap: Numap
    clank_cfg: Config
    clank_doc_assets: AssetPack
    pud_cfg: Config
    pud_doc_assets: AssetPack
    pud_content_assets: AssetPack

    def _reqs_from_fileset(self, cls: type[NewReq], fileset: Fileset) -> list[NewReq]:
        reqs = [cls(s, fileset.includes) for s in fileset.includes]
        if fileset.excludes:
            reqs.extend(cls(s, fileset.excludes) for s in fileset.excludes)
        return reqs

    def _reqs_from_resolvers(self, resolvers: list[Resolver]) -> list[NewReq]:
        reqs = []
        for res in resolvers:
            if isinstance(res, ManifestResolver):
                reqs.extend(self._reqs_from_fileset(FromPud, res.pud_fileset))
                reqs.extend(self._reqs_from_fileset(FromShared, res.shared_fileset))
            elif isinstance(res, RepoContentResolver):
                reqs.extend(self._reqs_from_fileset(FromPud, res.fileset))
        return reqs

    def _get_reqs(self, doms: list[Domain]) -> list[NewReq]:
        reqs: list[NewReq] = []
        for dom in doms:
            reqs.extend(self._reqs_from_resolvers(dom.resolvers))
            for prompt in dom.prompts:
                reqs.extend(self._reqs_from_resolvers(prompt.render.resolvers))
        return reqs

    def validate(self):
        doms = self.numap.get_entities(Domain)
        reqs = self._get_reqs(doms)

        pud_unsatisfied: list[NewReq] = []
        shared_unsatisfied: list[NewReq] = []

        for req in reqs:
            match req:
                case FromPud():
                    if self.pud_content_assets:
                        if not any(p.startswith(req.subject) for p in self.pud_content_assets.paths):
                            pud_unsatisfied.append(req)
                case FromShared():
                    if self.clank_doc_assets:
                        if not any(p.startswith(req.subject) for p in self.clank_doc_assets.paths):
                            shared_unsatisfied.append(req)

        
        self._handle_unsatisfied("pud content assetpack", pud_unsatisfied)
        self._handle_unsatisfied("shared assetpack", shared_unsatisfied)

    def _handle_unsatisfied(self, assetpack_name: str, unsatisfied: list[NewReq]):
        if not unsatisfied: return
        subjects = [req.subject for req in unsatisfied]
        self.ec.accept(UnsatisfiedFilesetSubjects(assetpack_name, subjects))
        for req in unsatisfied:
            req.target_container.remove(req.subject)

@dataclass
class NewReq:
    subject: str
    target_container: list[str]

@dataclass
class FromPud(NewReq): pass

@dataclass
class FromShared(NewReq): pass