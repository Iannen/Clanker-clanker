#!/usr/bin/env -S python3 -B
from core.engine import AppEngine
from adapters import LinuxDiskAdapter, LinuxTerminalAdapter, ScriptedTerminalAdapter, RuamelYamlParserAdapter
from modules import TUIServiceImpl, RenderServiceImpl, KBServiceImpl, IngestionServiceImpl
import sys
import traceback
import argparse
from pathlib import Path
from core import TestSequenceEnded

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
        exit_msg = engine.run()
        if is_test:
            io_adapter.end_test(exit_msg)
        else:
            print(exit_msg)
            
    except TestSequenceEnded as ex:
        if is_test:
            io_adapter.end_test(ex.__class__.__name__)
    except Exception as ex:
        sys.stderr.write("".join(traceback.format_exception(type(ex), ex, ex.__traceback__)))
        sys.exit(1)

if __name__ == "__main__":
    main()
