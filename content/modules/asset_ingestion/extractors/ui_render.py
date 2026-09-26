from stdlib import Any
from core import KBStateResolver, Render
from ...asset_ingestion import ErrorCollector, FilesetMap, FilelistMap, ValueExtractor, RenderParser


class UIRenderExtractorOld:
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

class UIRenderExtractor:
    def extract(
        self,
        sys_cfg: dict[str, Any],
        collector: ErrorCollector,
    ) -> Render:
        with collector.path("ui_render"):
            extractor = ValueExtractor()
            ui_render_dict = extractor.req_dict(sys_cfg, ["ui_render"])

            template = extractor.req_str(ui_render_dict, ["template"])
            inherit_base = extractor.req_bool(ui_render_dict, ["inherit_base"])
            inherit_domain = extractor.req_bool(ui_render_dict, ["inherit_domain"])
            #not solid below
            raw_resolvers = extractor.req_list(ui_render_dict, ["resolvers"])

            resolvers: list[KBStateResolver] = []
            for r_dict in raw_resolvers:
                res_type = extractor.req_str(r_dict, ["type"])
                anchor = extractor.req_str(r_dict, ["id"])

                if res_type in ("kb_info", "kb_state"):
                    resolvers.append(KBStateResolver(anchor=anchor))
                else:
                    collector.add_complaint(
                        f"Invalid resolver type '{res_type}' in ui_render; only 'kb_info' or 'kb_state' allowed."
                    )

            if len(resolvers) != 1:
                collector.add_complaint(
                    f"ui_render must carry exactly one KBStateResolver ('kb_info'), found {len(resolvers)}"
                )

            return Render(
                template=template,
                resolvers=resolvers,
                inherit_base=inherit_base,
                inherit_domain=inherit_domain,
            )