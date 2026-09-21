from typing import Any
from app import KBStateResolver, Render
from asset_ingestion import ErrorCollector, FilesetMap, FilelistMap, ValueExtractor, RenderParser


class UIRenderExtractor:
    def extract(
        self,
        sys_cfg: dict[str, Any],
        collector: ErrorCollector,
        unified_fsm: FilesetMap,
        unified_flm: FilelistMap | None = None,
    ) -> Render:
        with collector.path("ui_render"):
            ui_render_dict = ValueExtractor().req_dict(sys_cfg, ["ui_render"])
            ui_render = RenderParser(ui_render_dict, collector, unified_fsm, unified_flm).extract()
            kb_resolvers = [r for r in ui_render.resolvers if isinstance(r, KBStateResolver)]
            if len(kb_resolvers) != 1:
                collector.add_complaint(
                    f"ui_render must carry exactly one KBStateResolver ('kb_info'), found {len(kb_resolvers)}"
                )
            return ui_render