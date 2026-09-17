import os
from pathlib import Path
from app.constants import PathTokens
from app.exceptions import CorruptClanker, WorkspaceAlreadyInitialized, IllegalDuplicateFile
from ports_adapters.ports import DiskPort, NoSuchFile, FileAccessError

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
        # needs a new ex in port
        raise ValueError(f"Path does not start with a recognized BasePathToken: {tokenized_path}")

    def _read_path_as_string(self, target_path: Path) -> str:
        try:
            return target_path.read_text(encoding="utf-8")
        except FileNotFoundError as ex:
            raise NoSuchFile from ex
        except (PermissionError, UnicodeDecodeError) as ex:
            raise FileAccessError(f"File access error for {target_path}: {ex}") from ex

    def get_file_contents(self, tokenized_path: str) -> str:
        target_path = self._resolve_tokenized_path(tokenized_path)
        return self._read_path_as_string(target_path)

    def assert_dir_absent(self, tokenized_path: str) -> None:
        target_path = self._resolve_tokenized_path(tokenized_path)
        if target_path.exists() and target_path.is_dir():
            raise WorkspaceAlreadyInitialized(f"Workspace directory already exists: {target_path}")

    def assert_file_absent(self, tokenized_path: str) -> None:
        target_path = self._resolve_tokenized_path(tokenized_path)
        if target_path.exists() and target_path.is_file():
            raise WorkspaceAlreadyInitialized(f"Workspace file already exists: {target_path}")

    def copy_file(
        self, from_path: str, to_dir: str, from_ext: str = "", to_ext: str = ""
    ) -> None:
        src_path = self._resolve_tokenized_path(from_path)
        dest_dir = self._resolve_tokenized_path(to_dir)
        # can we provoke an ex, so we can raise NSF with cause?
        if not src_path.exists() or not src_path.is_file():
            raise NoSuchFile from ex

        filename = src_path.name
        if from_ext and to_ext and filename.endswith(from_ext):
            filename = filename[:-len(from_ext)] + to_ext

        dest_path = dest_dir / filename

        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            content = src_path.read_text(encoding="utf-8")
            dest_path.write_text(content, encoding="utf-8")
        except (PermissionError, UnicodeDecodeError) as ex:
            raise FileAccessError(f"Error copying file to {dest_path}: {ex}") from ex

    def is_cwd_script_dir(self) -> bool:
        return self.pud_path.resolve() == self.clanker_path.resolve()

    def read_asset(self, tokenized_path: str) -> str:
        return self.get_file_contents(tokenized_path)

    def get_files(
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
            raise ValueError(f"Unrecognized basepath token: {basepath_token}")

        resolved_files: set[str] = set()
        try:
            for root_str in rel_roots:
                rel_path = Path(root_str)
                full_path = base_dir / rel_path
                # can we provoke an ex, so we can raise NSF with cause?
                if not full_path.exists():
                    if missing_ok:
                        continue
                    raise NoSuchFile from ex

                if full_path.is_file():
                    resolved_files.add(str(rel_path))
                elif full_path.is_dir():
                    for file_path in full_path.rglob("*"):
                        if file_path.is_file():
                            resolved_files.add(str(file_path.relative_to(base_dir)))
        except (PermissionError, UnicodeDecodeError) as ex:
            raise FileAccessError(f"Error traversing directory under {basepath_token}: {ex}") from ex
        return resolved_files

    def get_contents_with_pud_fallback(self, file_names: list[str]) -> dict[str, str | None]:
        ret_map: dict[str, str | None] = {fn: None for fn in file_names}

        def _is_test_path(p: Path, base_path: Path) -> bool:
            try:
                rel_parts = p.relative_to(base_path).parts
                return rel_parts[0] == "test" or (len(rel_parts) > 1 and rel_parts[0:2] == ("content", "test"))
            except ValueError:
                return False

        try:
            shr_map: dict[str, Path] = {}
            if self.clanker_path.exists():
                for fn in file_names:
                    matches = [
                        p for p in self.clanker_path.rglob("*") 
                        if p.is_file() 
                        and p.name == fn 
                        and not any(part.startswith('.') for part in p.parts)
                        and not _is_test_path(p, self.clanker_path)
                    ]
                    if len(matches) > 1:
                        raise IllegalDuplicateFile(f"Collision in SHARED for '{fn}': {matches}")
                    elif len(matches) == 1:
                        shr_map[fn] = matches[0]

            pud_map: dict[str, Path] = {}
            if self.pud_path.exists():
                for fn in file_names:
                    matches = [
                        p for p in self.pud_path.rglob("*") 
                        if p.is_file() 
                        and p.name == fn
                        and not _is_test_path(p, self.pud_path)
                    ]
                    if len(matches) > 1:
                        raise IllegalDuplicateFile(f"Collision in PUD for '{fn}': {matches}")
                    elif len(matches) == 1:
                        pud_map[fn] = matches[0]

            resolved_paths: dict[str, Path] = {**shr_map, **pud_map}

            for fn, path in resolved_paths.items():
                if fn in ret_map:
                    ret_map[fn] = path.read_text(encoding="utf-8")
        except FileNotFoundError as ex:
            raise NoSuchFile from ex
        except (PermissionError, UnicodeDecodeError) as ex:
            raise FileAccessError(f"Access error during fallback lookup: {ex}") from ex

        return ret_map