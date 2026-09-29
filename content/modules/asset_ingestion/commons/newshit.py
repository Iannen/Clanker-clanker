from stdlib import dataclass

@dataclass
class MissingAsset: pass
@dataclass
class MalformedAsset: details: str


 
@dataclass(slots=True)
class Config:
    name: str
    path: str
    data: dict | MalformedAsset | MissingAsset

@dataclass
class AssetPack:
    name: str
    roots: list[str]
    paths: list[str] | None = None
    issue: str | None = None