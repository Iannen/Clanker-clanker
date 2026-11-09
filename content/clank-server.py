#!/usr/bin/env -S python3 -B

import sys
import traceback

from adapters import LinuxDiskAdapter, RuamelYamlParserAdapter
from modules import IngestionServiceImpl, KBServiceImpl, PromptServiceImpl
from backend import ClankServer


def main() -> None:
    files_adapter = LinuxDiskAdapter()
    cfg_ingestor = RuamelYamlParserAdapter()

    ingestion = IngestionServiceImpl(files=files_adapter, cfg_ingestor=cfg_ingestor)
    kb_service = KBServiceImpl()
    prompt_service = PromptServiceImpl(files=files_adapter)

    server = ClankServer(
        ingestion=ingestion,
        kb_service=kb_service,
        prompt_service=prompt_service,
    )
    server.run()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.stderr.write("".join(traceback.format_exception(type(sys.exc_info()[0]), sys.exc_info()[1], sys.exc_info()[2])))
        sys.exit(1)