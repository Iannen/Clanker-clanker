#!/usr/bin/env -S python3 -B
from ports_adapters.disk_adapter import LinuxDiskAdapter
from ports_adapters.terminal.linux import LinuxTerminalAdapter
from ports_adapters.terminal.scripted_terminal_adapter import ScriptedIOBridge
from ports_adapters.yaml_parser import RuamelYamlParserAdapter
from app.engine import AppEngine, ExceptionPolicy
from render_pipeline.render_service import RenderServiceImpl
from asset_ingestion.ingestion_service import IngestionServiceImpl
from keyboard.keyboard_service import KBServiceImpl
from tui.tui_service import TUIServiceImpl
import sys
import traceback
import argparse

def main():
    parser = argparse.ArgumentParser(description="Clanker TUI Engine")
    parser.add_argument("--test", action="store_true", help="Run in headless test mode")
    parser.add_argument("--input-script", nargs="+", default=["q"], help="Pre-recorded key sequence for test mode")
    parser.add_argument("--report-path", default="content/test/reports/latest_run.json", help="Path to output test report")
    args = parser.parse_args()

    try:
        files_adapter = ExceptionPolicy.protect_adapter(LinuxDiskAdapter())
        
        # Select IO bridge based on test mode flag
        if args.test:
            io_adapter = ExceptionPolicy.protect_adapter(
                ScriptedIOBridge(input_sequence=args.input_script, report_path=args.report_path)
            )
        else:
            io_adapter = ExceptionPolicy.protect_adapter(LinuxTerminalAdapter())
            
        cfg_ingestor = ExceptionPolicy.protect_adapter(RuamelYamlParserAdapter())

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