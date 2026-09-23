#!/usr/bin/env -S python3 -B
from core.engine import AppEngine
from adapters import LinuxDiskAdapter, LinuxTerminalAdapter, ScriptedTerminalAdapter, RuamelYamlParserAdapter
from modules import TUIServiceImpl, RenderServiceImpl, KBServiceImpl, IngestionServiceImpl
import sys
import traceback
import argparse

def _bootstrap_io_adapter():
    parser = argparse.ArgumentParser(description="Clanker TUI Engine")
    parser.add_argument("--test", action="store_true", help="Run in headless test mode")
    parser.add_argument(
        "--input-script",
        nargs="*",
        default=[],
        help="Pre-recorded key sequence for test mode",
    )
    parser.add_argument(
        "--report-path", 
        default="content/test/reports/latest_run.json", 
        help="Path to output test report"
    )
    args = parser.parse_args()

    if args.test:
        adapter = ScriptedTerminalAdapter(
            input_sequence=args.input_script,
            sandbox_dir=args.report_path
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

    if not is_test:
        try:
            exit_msg = engine.run()
            if exit_msg:
                print(exit_msg)
        except Exception as ex:
            sys.stderr.write("\n[CRITICAL FAILURE] The ex architecture has failed: \n\n")
            traceback.print_exception(type(ex), ex, ex.__traceback__, file=sys.stderr)
    else:
        try:
            exit_msg = engine.run()
            io_adapter.flush_report(
                exit_code=0,
                stdout=exit_msg,
                stderr=None
            )
        #except TestSequenceEnded as test_end:
            #io_adapter.flush_report(
                #exit_code=0,
                #stdout= None, 
                #stderr=TestSequenceEnded.__name__
            #)
        except Exception as ex:
            tb_str = "".join(traceback.format_exception(type(ex), ex, ex.__traceback__))
            io_adapter.flush_report(
                exit_code=1,
                stdout=None,
                stderr=f"{ex}\n\nTraceback:\n{tb_str}"
            )

if __name__ == "__main__":
    main()