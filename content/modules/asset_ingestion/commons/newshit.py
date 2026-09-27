from stdlib import dataclass

@dataclass(slots=True)
class Config:
    name: str
    path: str
    data: dict | None = None
    issue: str | None = None

@dataclass
class AssetPack:
    name: str
    roots: list[str]
    paths: list[str] | None = None
    issue: str | None = None