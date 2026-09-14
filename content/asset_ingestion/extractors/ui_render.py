from typing import Any
from app.models import KBStateResolver, Render
from asset_ingestion.commons.error_collector import ErrorCollector
from asset_ingestion.commons.fileset_map import FilesetMap
from asset_ingestion.commons.value_extractor import ValueExtractor
from asset_ingestion.parsers.render import RenderParser


class UIRenderExtractor:
    def extract(
        self,
        sys_cfg: dict[str, Any],
        collector: ErrorCollector,
        unified_fsm: FilesetMap,
    ) -> Render:
        with collector.path("ui_render"):
            ui_render_dict = ValueExtractor().req_dict(sys_cfg, ["ui_render"])
            ui_render = RenderParser(ui_render_dict, collector, unified_fsm).extract()
            kb_resolvers = [r for r in ui_render.resolvers if isinstance(r, KBStateResolver)]
            if len(kb_resolvers) != 1:
                collector.add_complaint(
                    f"ui_render must carry exactly one KBStateResolver ('kb_info'), found {len(kb_resolvers)}"
                )
            return ui_render