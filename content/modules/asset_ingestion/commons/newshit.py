from stdlib import dataclass

@dataclass(slots=True)
class Config:
    name: str
    path: str
    data: dict | None
@dataclass
class AssetPack:
    name: str
    roots: list[str]
    paths: list[str] | None