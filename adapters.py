from __future__ import annotations

import base64
import os
import sys
import termios
import tty
from pathlib import Path
from ruamel.yaml import YAML

from clanker import FileBridgePort, IOBridgePort, IllegalDuplicateFile, CorruptClanker

class IOBridge(IOBridgePort): 
    def clear(self) -> None:
        os.system("clear")

    def to_clipboard(self, text_content: str) -> int:
        payload = base64.b64encode(text_content.encode("utf-8")).decode("utf-8")
        sys.stdout.write(f"\033]52;c;{payload}\007")
        sys.stdout.flush()
        return len(text_content.splitlines())

    def write(self, text: str) -> None:
        print(text, end="", flush=True)

    def read_char(self) -> str:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

class FileBridge(FileBridgePort):
    def __init__(self) -> None:
        self.clanker_path = Path(os.path.realpath(__file__)).parent
        self.pud_path = Path.cwd()
        self.yaml = YAML()

    def pud_cfg_frag(self, rel_path: str) -> dict:
        return self.yaml.load((self.pud_path / rel_path).read_text(encoding="utf-8"))

    def clank_cfg_frag(self, rel_path: str) -> dict:
        return self.yaml.load((self.clanker_path / rel_path).read_text(encoding="utf-8"))

    def write_default_documents(
        self, doc_templ_dir: str, pud_doc_dir: str, templ_ext: str, doc_ext: str
    ) -> None:
        prog_doc_dir = self.pud_path / pud_doc_dir
        prompt_frag_dir = self.pud_path / ".clanker" / "prompt-fragments"
        prog_doc_dir.mkdir(parents=True, exist_ok=True)
        prompt_frag_dir.mkdir(parents=True, exist_ok=True)

        doc_templates_dir = self.clanker_path / doc_templ_dir
        if not doc_templates_dir.exists():
            raise CorruptClanker(f"Template directory missing: '{doc_templates_dir}'")

        templates = list(doc_templates_dir.glob(f"*{templ_ext}"))
        if not templates:
            raise CorruptClanker(f"No '{templ_ext}' template files found in '{doc_templates_dir}'")

        for template_path in templates:
            target_filename = template_path.stem + doc_ext
            target_path = prog_doc_dir / target_filename
            if not target_path.exists():
                content = template_path.read_text(encoding="utf-8")
                target_path.write_text(content, encoding="utf-8")

    def is_cwd_script_dir(self) -> bool:
        return self.pud_path.resolve() == self.clanker_path.resolve()

    def write_yaml(self, rel_path: Path, data: dict) -> None:
        target_path = self.pud_path / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            self.yaml.dump(data, f)

    def read_clanker_asset(self, rel_path: str) -> str:
        return (self.clanker_path / rel_path).read_text(encoding="utf-8")

    def read_pud_asset(self, rel_path: Path) -> str:
        return (self.pud_path / rel_path).read_text(encoding="utf-8")

    def write_content(self, rel_path: Path, content: str) -> None:
        target_path = self.pud_path / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")

    def get_pud_files(self, rel_roots: list[str | Path]) -> set[Path]:
        resolved_files: set[Path] = set()
        for root_str in rel_roots:
            rel_path = Path(root_str)
            full_path = self.pud_path / rel_path

            if not full_path.exists():
                raise FileNotFoundError(rel_path)

            if full_path.is_file():
                resolved_files.add(rel_path)
            elif full_path.is_dir():
                for file_path in full_path.rglob("*"):
                    if file_path.is_file():
                        resolved_files.add(file_path.relative_to(self.pud_path))
        return resolved_files

    def getAssetMap(self) -> dict[str, Path]:
        clank_map: dict[str, Path] = {}
        clanker_dot_dir = self.clanker_path / ".clanker"
        if clanker_dot_dir.exists():
            for path in clanker_dot_dir.rglob("*"):
                if path.is_file():
                    filename = path.name
                    if filename in clank_map:
                        raise IllegalDuplicateFile(
                            f"Clanker asset collision: {clank_map[filename]} {path}"
                        )
                    clank_map[filename] = path

        pud_map: dict[str, Path] = {}
        pud_dot_dir = self.pud_path / ".clanker"
        if pud_dot_dir.exists():
            for path in pud_dot_dir.rglob("*"):
                if path.is_file():
                    filename = path.name
                    if filename in pud_map:
                        raise IllegalDuplicateFile(
                            f"PUD asset collision: {pud_map[filename]} {path}"
                        )
                    pud_map[filename] = path

        clank_map.update(pud_map)
        return clank_map

    def getFileContent(self, full_path: Path | str) -> str:
        return Path(full_path).read_text(encoding="utf-8")