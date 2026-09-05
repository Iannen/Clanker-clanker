from __future__ import annotations

import base64
import os
import sys
import termios
import tty
from pathlib import Path
from ruamel.yaml import YAML
from models import *

class IOBridge:
    def to_clipboard(self, text_content: str) -> int:
        payload = base64.b64encode(text_content.encode("utf-8")).decode("utf-8")
        sys.stdout.write(f"\033]52;c;{payload}\007")
        sys.stdout.flush()
        return len(text_content.splitlines())

    def write(self, text: str) -> None:
        os.system("clear")
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

    def get_acceptance(self, required_phrase: str | None) -> tuple[str, str]:
        if required_phrase is None:
            while True:
                ch = self.read_char()
                if ch in IOControl.ABORT_KEYS:
                    return (IOControl.DECLINED, "")
                if ch == IOControl.ACCEPT_KEY:
                    return (IOControl.ACCEPTED, "")

        buffer = ""
        while True:
            ch = self.read_char()
            if ch in IOControl.ABORT_KEYS:
                return (IOControl.DECLINED, "")
            if ch == IOControl.ACCEPT_KEY:
                if buffer == required_phrase:
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                    return (IOControl.ACCEPTED, "")
                return (IOControl.INVALID, buffer)
            if ch in IOControl.BACKSPACE_KEYS:
                if len(buffer) > 0:
                    buffer = buffer[:-1]
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
            elif ch.isprintable():
                buffer += ch
                sys.stdout.write(ch)
                sys.stdout.flush()

class FileBridge:
    def __init__(self) -> None:
        self.clanker_path = Path(os.path.realpath(__file__)).parent
        self.pud_path = Path.cwd()
        self.yaml = YAML()

    def _pud_file_as_string(self, rel_path: str) -> str:
        return (self.pud_path / rel_path).read_text(encoding="utf-8")

    def _shared_file_as_string(self, rel_path: str) -> str:
        return (self.clanker_path / rel_path).read_text(encoding="utf-8")

    def get_file_contents(self, tokenized_path: str) -> str:
        if tokenized_path.startswith(BasePathTokens.PUD):
            rel_path = tokenized_path[len(BasePathTokens.PUD):].lstrip("/")
            return self._pud_file_as_string(rel_path)
        elif tokenized_path.startswith(BasePathTokens.SHARED):
            rel_path = tokenized_path[len(BasePathTokens.SHARED):].lstrip("/")
            return self._shared_file_as_string(rel_path)
        raise ValueError(f"Path does not start with a recognized BasePathToken: {tokenized_path}")

    def write_default_documents(
        self, doc_templ_dir: str, pud_doc_dir: str, templ_ext: str, doc_ext: str
    ) -> None:
        prog_doc_dir = self.pud_path / pud_doc_dir.lstrip("/")
        prompt_frag_dir = self.pud_path / ".clanker" / "prompt-fragments"
        prog_doc_dir.mkdir(parents=True, exist_ok=True)
        prompt_frag_dir.mkdir(parents=True, exist_ok=True)

        doc_templates_dir = self.clanker_path / doc_templ_dir.lstrip("/")
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

    def write_yaml(self, tokenized_path: str, data: dict) -> None:
        if tokenized_path.startswith(BasePathTokens.PUD):
            rel_path = tokenized_path[len(BasePathTokens.PUD):].lstrip("/")
            target_path = self.pud_path / rel_path
        elif tokenized_path.startswith(BasePathTokens.SHARED):
            rel_path = tokenized_path[len(BasePathTokens.SHARED):].lstrip("/")
            target_path = self.clanker_path / rel_path
        else:
            raise ValueError(f"Path does not start with a recognized BasePathToken: {tokenized_path}")

        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            self.yaml.dump(data, f)

    def read_asset(self, tokenized_path: str | Path) -> str:
        str_path = str(tokenized_path)
        if str_path.startswith(BasePathTokens.PUD):
            rel_path = str_path[len(BasePathTokens.PUD):].lstrip("/")
            return self._pud_file_as_string(rel_path)
        elif str_path.startswith(BasePathTokens.SHARED):
            rel_path = str_path[len(BasePathTokens.SHARED):].lstrip("/")
            return self._shared_file_as_string(rel_path)
        raise ValueError(f"Path does not start with a recognized BasePathToken: {str_path}")

    def get_files(
        self,
        basepath_token: str,
        rel_roots: list[str | Path],
        missing_ok: bool = False
    ) -> set[Path]:
        if basepath_token == BasePathTokens.PUD:
            base_dir = self.pud_path
        elif basepath_token == BasePathTokens.SHARED:
            base_dir = self.clanker_path
        else:
            raise ValueError(f"Unrecognized basepath token: {basepath_token}")

        resolved_files: set[Path] = set()
        for root_str in rel_roots:
            rel_path = Path(root_str)
            full_path = base_dir / rel_path

            if not full_path.exists():
                if missing_ok:
                    continue
                raise FileNotFoundError(rel_path)

            if full_path.is_file():
                resolved_files.add(rel_path)
            elif full_path.is_dir():
                for file_path in full_path.rglob("*"):
                    if file_path.is_file():
                        resolved_files.add(file_path.relative_to(base_dir))
        return resolved_files

    def get_contents_with_pud_fallback(self, file_names: list[str]) -> dict[str, str | None]:
        ret_map: dict[str, str | None] = {fn: None for fn in file_names}

        shr_map: dict[str, Path] = {}
        shr_dir = self.clanker_path / ".clanker"
        if shr_dir.exists():
            for fn in file_names:
                matches = [p for p in shr_dir.rglob("*") if p.is_file() and p.name == fn]
                if len(matches) > 1:
                    raise IllegalDuplicateFile(f"Collision in SHARED for '{fn}': {matches}")
                elif len(matches) == 1:
                    shr_map[fn] = matches[0]

        pud_map: dict[str, Path] = {}
        pud_dir = self.pud_path / ".clanker"
        if pud_dir.exists():
            for fn in file_names:
                matches = [p for p in pud_dir.rglob("*") if p.is_file() and p.name == fn]
                if len(matches) > 1:
                    raise IllegalDuplicateFile(f"Collision in PUD for '{fn}': {matches}")
                elif len(matches) == 1:
                    pud_map[fn] = matches[0]

        resolved_paths: dict[str, Path] = {**shr_map, **pud_map}

        for fn, path in resolved_paths.items():
            if fn in ret_map:
                ret_map[fn] = path.read_text(encoding="utf-8")

        return ret_map

    def getFileContent(self, full_path: Path | str) -> str:
        return Path(full_path).read_text(encoding="utf-8")