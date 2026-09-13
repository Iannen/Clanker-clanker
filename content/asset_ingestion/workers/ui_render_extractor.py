from typing import Any
from app.models import KBStateResolver, Render, Resolver
from asset_ingestion.commons.error_collector import ErrorCollector
from asset_ingestion.commons.value_extractor import ValueExtractor


class UIRenderExtractor:
    def __init__(
        self,
        sys_cfg: dict[str, Any],
        collector: ErrorCollector,
    ) -> None:
        self.sys_cfg = sys_cfg
        self.collector = collector
        self.extractor = ValueExtractor()

    def extract(self) -> Render:
        self.collector.push_path("ui_render")
        try:
            ui_render_dict = self.extractor.req_dict(self.sys_cfg, ["ui_render"])
            return self._build_render(ui_render_dict)
        finally:
            self.collector.pop_path()

    def _build_render(self, render_dict: dict[str, Any]) -> Render:
        template = self.extractor.req_str(render_dict, ["template"], Render.template)
        inherit_base = self.extractor.req_bool(render_dict, ["inherit_base"], Render.inherit_base)
        inherit_domain = self.extractor.req_bool(render_dict, ["inherit_domain"], Render.inherit_domain)
        raw_resolvers = self.extractor.req_list(render_dict, ["resolvers"])
        resolvers = [r for r in (self._build_resolver(r) for r in raw_resolvers) if r is not None]
        return Render(
            template=template,
            resolvers=resolvers,
            inherit_base=inherit_base,
            inherit_domain=inherit_domain,
        )

    def _build_resolver(self, data: dict[str, Any]) -> Resolver | None:
        res_type = self.extractor.req_str(data, ["type"])
        anchor = self.extractor.req_str(data, ["id"])

        if res_type in ("kb_info", "kb_state"):
            return KBStateResolver(anchor=anchor)

        self.collector.add_complaint(
            f"Unsupported resolver type '{res_type}' in ui_render. Expected 'kb_info' or 'kb_state'."
        )
        return None