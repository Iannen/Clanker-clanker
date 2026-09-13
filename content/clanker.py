#!/usr/bin/env -S python3 -B
from adapters.adapters import FileBridge, IOBridge, ConfigIngestor
from render_pipeline.code import DefaultContentShaper
from asset_ingestion.ingestion_service import IngestionServiceImpl
from asset_ingestion.code import RuntimeConfigAssembler
from app.engine import AppEngine, ExceptionPolicy, AssemblyService, IOService
import sys
import traceback

def main():
    try:
        files_adapter = ExceptionPolicy.protect_adapter(FileBridge())
        io_adapter = ExceptionPolicy.protect_adapter(IOBridge())
        cfg_ingestor = ExceptionPolicy.protect_adapter(ConfigIngestor())
        shaper = DefaultContentShaper()

        assembler = RuntimeConfigAssembler()

        ingestion = IngestionServiceImpl(files=files_adapter, cfg_ingestor=cfg_ingestor, assembler=assembler)
        renderer = AssemblyService(files=files_adapter, shaper=shaper)
        io = IOService(io_bridge=io_adapter)

        engine = AppEngine(
            io=io,
            session=ingestion,
            renderer=renderer
        )

        exit_msg = engine.run()
        print(exit_msg)

    except Exception as ex:
        sys.stderr.write("\n[CRITICAL FAILURE] The ex architecture has failed: \n\n")
        traceback.print_exception(type(ex), ex, ex.__traceback__, file=sys.stderr)

if __name__ == "__main__":
    main()