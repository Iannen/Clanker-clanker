from core import ManifestResolver, RepoContentResolver, Fileset
from stdlib import dataclass
from ...asset_ingestion import ErrorCollector, Numap, UnsatisfiedFilesetSubjects, AssetPack

@dataclass
class FilesetValidator2:
    ec: ErrorCollector
    numap: Numap
    clank_doc_assets: AssetPack 
    pud_content_assets: AssetPack 

    def _reqs_from_fileset(self, cls: type[NewReq], fileset: Fileset) -> list[NewReq]:
        subjects = fileset.includes + fileset.excludes if fileset.excludes else fileset.includes
        reqs = [cls(s, fileset.includes) for s in fileset.includes]
        if fileset.excludes:
            reqs.extend(cls(s, fileset.excludes) for s in fileset.excludes)
        return reqs

    def validate(self):
        reqs: list[NewReq] = []

        for res in self.numap.get_entities(ManifestResolver):
            reqs.extend(self._reqs_from_fileset(FromPud, res.pud_fileset))
            reqs.extend(self._reqs_from_fileset(FromShared, res.shared_fileset))

        for res in self.numap.get_entities(RepoContentResolver):
            reqs.extend(self._reqs_from_fileset(FromPud, res.fileset))

        pud_unsatisfied = [
            req for req in reqs
            if isinstance(req, FromPud) and self.pud_content_assets
            and not any(p.startswith(req.subject) for p in self.pud_content_assets.paths)
        ]
        shared_unsatisfied = [
            req for req in reqs
            if isinstance(req, FromShared) and self.clank_doc_assets
            and not any(p.startswith(req.subject) for p in self.clank_doc_assets.paths)
        ]

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