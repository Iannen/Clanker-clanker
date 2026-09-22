import os
from pathlib import Path
from core.engine_deps import DiskPort, NoSuchFile, AssetExists, FileAccessError, InvalidPathToken
from core import PathTokens

class LinuxDiskAdapter(DiskPort):
    def __init__(self) -> None:
        self.clanker_path = Path(os.path.realpath(__file__)).parent.parent.parent
        self.pud_path = Path.cwd()

    def _resolve_tokenized_path(self, tokenized_path: str) -> Path:
        str_path = str(tokenized_path)
        if str_path.startswith(PathTokens.PUD):
            rel_path = str_path[len(PathTokens.PUD):].lstrip("/")
            return self.pud_path / rel_path
        elif str_path.startswith(PathTokens.SHARED):
            rel_path = str_path[len(PathTokens.SHARED):].lstrip("/")
            return self.clanker_path / rel_path
        raise InvalidPathToken from ValueError(f"Path does not start with a recognized BasePathToken: {tokenized_path}")

    def _read_path_as_string(self, target_path: Path) -> str:
        try:
            return target_path.read_text(encoding="utf-8")
        except FileNotFoundError as ex:
            raise NoSuchFile from ex
        except (PermissionError, UnicodeDecodeError) as ex:
            raise FileAccessError from ex

    def get_file_contents(self, tokenized_path: str) -> str:
        target_path = self._resolve_tokenized_path(tokenized_path)
        return self._read_path_as_string(target_path)

    def assert_absent(self, tokenized_path: str) -> None:
        target_path = self._resolve_tokenized_path(tokenized_path)
        if target_path.exists():
            raise AssetExists from ValueError(f"Target already exists: {target_path}")

    def create_dir(self, tokenized_path: str) -> None:
        target_path = self._resolve_tokenized_path(tokenized_path)
        try:
            target_path.mkdir(parents=True, exist_ok=True)
        except (PermissionError, UnicodeDecodeError) as ex:
            raise FileAccessError from ex

    def copy_file(
        self, from_path: str, to_path: str
    ) -> None:
        src_path = self._resolve_tokenized_path(from_path)
        dest_path = self._resolve_tokenized_path(to_path)
        if not src_path.exists() or not src_path.is_file():
            raise NoSuchFile from FileNotFoundError(f"Source file does not exist: {src_path}")

        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            content = src_path.read_text(encoding="utf-8")
            dest_path.write_text(content, encoding="utf-8")
        except (PermissionError, UnicodeDecodeError) as ex:
            raise FileAccessError from ex
    def is_cwd_script_dir(self) -> bool:
        return self.pud_path.resolve() == self.clanker_path.resolve()

    def read_asset(self, tokenized_path: str) -> str:
        return self.get_file_contents(tokenized_path)

    def get_file_paths(
        self,
        basepath_token: str,
        rel_roots: list[str],
        missing_ok: bool = False
    ) -> set[str]:
        if basepath_token == PathTokens.PUD:
            base_dir = self.pud_path
        elif basepath_token == PathTokens.SHARED:
            base_dir = self.clanker_path
        else:
            raise InvalidPathToken from ValueError(f"Unrecognized basepath token: {basepath_token}")

        resolved_files: set[str] = set()
        try:
            for root_str in rel_roots:
                rel_path = Path(root_str)
                full_path = base_dir / rel_path
                if not full_path.exists():
                    if missing_ok:
                        continue
                    raise NoSuchFile from FileNotFoundError(f"Path does not exist: {full_path}")

                if full_path.is_file():
                    resolved_files.add(str(rel_path))
                elif full_path.is_dir():
                    for file_path in full_path.rglob("*"):
                        if file_path.is_file():
                            resolved_files.add(str(file_path.relative_to(base_dir)))
        except (PermissionError, UnicodeDecodeError) as ex:
            raise FileAccessError from ex
        return resolved_files

    def get_dir_manifest(
        self,
        basepath_token: str,
        rel_roots: list[str]
    ) -> set[str]:
        if basepath_token == PathTokens.PUD:
            base_dir = self.pud_path
        elif basepath_token == PathTokens.SHARED:
            base_dir = self.clanker_path
        else:
            raise InvalidPathToken from ValueError(f"Unrecognized basepath token: {basepath_token}")

        resolved_files: set[str] = set()
        try:
            for root_str in rel_roots:
                rel_path = Path(root_str)
                full_path = base_dir / rel_path
                if not full_path.exists():
                    raise NoSuchFile from FileNotFoundError(f"Path does not exist: {full_path}")

                if full_path.is_file():
                    resolved_files.add(str(rel_path))
                elif full_path.is_dir():
                    if not any(full_path.iterdir()):
                        resolved_files.add(str(rel_path))
                    else:
                        for sub_path in full_path.rglob("*"):
                            if sub_path.is_file() or (sub_path.is_dir() and not any(sub_path.iterdir())):
                                resolved_files.add(str(sub_path.relative_to(base_dir)))
        except (PermissionError, UnicodeDecodeError) as ex:
            raise FileAccessError from ex
        return resolved_files