#!/usr/bin/env -S python3 -B
from core.engine import AppEngine
from adapters import LinuxDiskAdapter, LinuxTerminalAdapter, ScriptedTerminalAdapter, RuamelYamlParserAdapter, TestSequenceEnded
from modules import FrontendServiceImpl, PromptServiceImpl, KBServiceImpl, IngestionServiceImpl, WebFrontendServiceImpl
from web_clanker import WebServer
import sys
import traceback
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Clanker TUI Engine")
    sub = parser.add_subparsers(dest="mode")

    test_sub = sub.add_parser("test", help="Run in headless test mode")
    test_sub.add_argument(
        "--input-script",
        nargs="*",
        required=True,
        help="Pre-recorded key sequence for test mode",
    )
    test_sub.add_argument(
        "--framedump-path",
        type=str,
        required=True,
        help="Target filepath for execution frames report",
    )

    sub.add_parser("server", help="Start the web control server")
    sub.add_parser("newserver", help="Start the web frontend (new)")

    args = parser.parse_args()

    if args.mode == "newserver":
        files_adapter = LinuxDiskAdapter()
        cfg_ingestor = RuamelYamlParserAdapter()
        ingestion = IngestionServiceImpl(files=files_adapter, cfg_ingestor=cfg_ingestor)
        prompt_service = PromptServiceImpl(files=files_adapter)
        kb_service = KBServiceImpl()
        frontend = WebFrontendServiceImpl(
            port=8787,
            gpu_box_url="https://gpu-box.tailca68f1.ts.net:8787",
        )
        frontend.start()
        engine = AppEngine(
            frontend=frontend,
            kb_service=kb_service,
            ingestion=ingestion,
            prompt_service=prompt_service,
        )
        engine.run()
        return

    if args.mode == "server":
        files_adapter = LinuxDiskAdapter()
        cfg_ingestor = RuamelYamlParserAdapter()
        ingestion = IngestionServiceImpl(files=files_adapter, cfg_ingestor=cfg_ingestor)
        prompt_service = PromptServiceImpl(files=files_adapter)
        kb_service = KBServiceImpl()
        server = WebServer(
            ingestion=ingestion,
            prompt_service=prompt_service,
            kb_service=kb_service,
            port=8787,
            gpu_box_url="https://gpu-box.tailca68f1.ts.net:8787",
        )
        server.run()
        return

    if args.mode == "test":
        io_adapter = ScriptedTerminalAdapter(
            input_sequence=args.input_script,
            framedump_path=Path(args.framedump_path),
        )
        is_test = True
    else:
        io_adapter = LinuxTerminalAdapter()
        is_test = False

    files_adapter = LinuxDiskAdapter()
    cfg_ingestor = RuamelYamlParserAdapter()

    ingestion = IngestionServiceImpl(files=files_adapter, cfg_ingestor=cfg_ingestor)
    prompt_service = PromptServiceImpl(files=files_adapter)
    io = FrontendServiceImpl(io_adapter, files_adapter)
    kb_service = KBServiceImpl()

    engine = AppEngine(frontend=io, kb_service=kb_service, ingestion=ingestion, prompt_service=prompt_service)
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