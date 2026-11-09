#!/usr/bin/env -S python3 -B
"""Standalone Clanker server entrypoint.

Boots ingestion, then DI-injects the class-based server and runs it.
"""

import sys
import traceback

from adapters import LinuxDiskAdapter, RuamelYamlParserAdapter
from modules import IngestionServiceImpl, KBServiceImpl, PromptServiceImpl
from core.engine_deps import StartCmd, StartResult, ClankerizeResult, TerminateResult
from backend import ClankServer


def main() -> None:
    # 1. Instantiate adapters
    files_adapter = LinuxDiskAdapter()
    cfg_ingestor = RuamelYamlParserAdapter()

    # 2. Run ingestion
    ingestion = IngestionServiceImpl(files=files_adapter, cfg_ingestor=cfg_ingestor)
    result = ingestion.get_runtime_config()

    # 3. Handle clankerize if needed
    if isinstance(result, ClankerizeResult):
        result = ingestion.initialize_workspace()

    if isinstance(result, TerminateResult):
        sys.stderr.write(f"Boot failed: {result.report.get_critical_complaints()}\n")
        sys.exit(1)

    if not isinstance(result, (StartCmd, StartResult)):
        sys.stderr.write(f"Unexpected boot result: {type(result).__name__}\n")
        sys.exit(1)

    # 4. Build services
    kb_service = KBServiceImpl()
    prompt_service = PromptServiceImpl(files=files_adapter)

    start_cmd = StartCmd(kb=result.kb, ui_render=result.ui_render)
    bootstrap = kb_service.handle_start(start_cmd)

    boot_message = "Bootstrap completed successfully"
    if isinstance(result, StartResult) and result.report.get_all_complaints():
        boot_message = f"Bootstrap completed with {len(result.report.get_all_complaints())} soft complaint(s)"

    # 5. DI + run
    server = ClankServer(
        kb_service=kb_service,
        prompt_service=prompt_service,
        boot_message=boot_message,
    )
    server.run()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.stderr.write("".join(traceback.format_exception(type(sys.exc_info()[0]), sys.exc_info()[1], sys.exc_info()[2])))
        sys.exit(1)