#!/usr/bin/env -S python3 -B
from core.engine import AppEngine
from adapters import LinuxDiskAdapter, LinuxTerminalAdapter, ScriptedTerminalAdapter, RuamelYamlParserAdapter
from modules import TUIServiceImpl, RenderServiceImpl, KBServiceImpl, IngestionServiceImpl
import sys
import traceback
import argparse

def main():
    parser = argparse.ArgumentParser(description="Clanker TUI Engine")
    parser.add_argument("--test", action="store_true", help="Run in headless test mode")
    parser.add_argument(
        "--input-script",
        nargs="*",
        default=[],
        help="Pre-recorded key sequence for test mode",
    )
    parser.add_argument("--report-path", default="content/test/reports/latest_run.json", help="Path to output test report")
    args = parser.parse_args()

    try:
        files_adapter = LinuxDiskAdapter()
 
        if args.test:
            io_adapter = ScriptedTerminalAdapter(args.input_script, args.report_path)
        else:
            io_adapter = LinuxTerminalAdapter()
            
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

        exit_msg = engine.run()
        print(exit_msg)

    except Exception as ex:
        sys.stderr.write("\n[CRITICAL FAILURE] The ex architecture has failed: \n\n")
        traceback.print_exception(type(ex), ex, ex.__traceback__, file=sys.stderr)

if __name__ == "__main__":
    main()