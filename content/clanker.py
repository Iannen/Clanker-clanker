#!/usr/bin/env -S python3 -B
from ports_adapters.disk_adapter import LinuxDiskAdapter
from ports_adapters.terminal_adapter import LinuxTerminalAdapter
from ports_adapters.yaml_parser import RuamelYamlParserAdapter
from app.engine import AppEngine, ExceptionPolicy
from render_pipeline.render_service import RenderServiceImpl
from asset_ingestion.ingestion_service import IngestionServiceImpl
from keyboard.keyboard_service import KBServiceImpl
from tui.tui_service import TUIServiceImpl
import sys
import traceback

def main():
    try:
        #adapter instantiaon - later pick 'em based on os environment
        files_adapter = ExceptionPolicy.protect_adapter(LinuxDiskAdapter())
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