#!/usr/bin/env -S python3 -B
from core.engine import AppEngine
from adapters import LinuxDiskAdapter, LinuxTerminalAdapter, ScriptedTerminalAdapter, RuamelYamlParserAdapter
from modules import TUIServiceImpl, RenderServiceImpl, KBServiceImpl, IngestionServiceImpl
import sys
import traceback
import argparse
from pathlib import Path

def _bootstrap_io_adapter():
    is_test_mode = "--test" in sys.argv

    parser = argparse.ArgumentParser(description="Clanker TUI Engine")
    parser.add_argument("--test", action="store_true", help="Run in headless test mode")
    parser.add_argument(
        "--input-script",
        nargs="*",
        required=is_test_mode,
        help="Pre-recorded key sequence for test mode",
    )
    parser.add_argument(
        "--framedump-path",
        type=str,
        required=is_test_mode,
        help="Target filepath for execution frames report",
    )
    args = parser.parse_args()

    if args.test:
        adapter = ScriptedTerminalAdapter(
            input_sequence=args.input_script,
            framedump_path=Path(args.framedump_path),
        )
        return True, adapter

    return False, LinuxTerminalAdapter()

def main():
    is_test, io_adapter = _bootstrap_io_adapter()

    files_adapter = LinuxDiskAdapter()
    cfg_ingestor = RuamelYamlParserAdapter()

    ingestion = IngestionServiceImpl(files=files_adapter, cfg_ingestor=cfg_ingestor)
    renderer = RenderServiceImpl(files=files_adapter)
    io = TUIServiceImpl(io_bridge=io_adapter)
    kb_service = KBServiceImpl()

    engine = AppEngine(
        io=io,
        session=ingestion,
        renderer=renderer,
        kb_service=kb_service
    )
    try: 
        output = engine.run()
        exit_code = 0
        if is_test:
            io_adapter.flush_report(exit_code=0, stdout=output)
        else:
            sys.stdout.write(f"{output}\n")

    except Exception as ex:
        output = "".join(traceback.format_exception(type(ex), ex, ex.__traceback__))
        if is_test:
            io_adapter.flush_report(exit_code=1, stderr=output)
        sys.stderr.write(output)

if __name__ == "__main__":
    main()
