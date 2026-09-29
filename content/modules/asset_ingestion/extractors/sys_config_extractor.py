from stdlib import dataclass
from core import KBStateResolver, Render, Button
from ...asset_ingestion import ErrorCollector, ValueExtractor, Config

@dataclass
class SysConfigExtractor:
    collector: ErrorCollector
    extractor = ValueExtractor()
    def extract(
        self,
        sys_cfg: Config,
    ) -> tuple[Render, dict[str, Button]]: 
        ui_render = self._get_render(sys_cfg)
        bnt_map = self._get_btn_map(sys_cfg)
        return ui_render, bnt_map

    def _get_render(self, sys_cfg):
        with self.collector.path("ui_render"):
            ui_render_dict = self.extractor.req_dict(sys_cfg.data, ["ui_render"])

            template = self.extractor.req_str(ui_render_dict, ["template"])
            inherit_base = self.extractor.req_bool(ui_render_dict, ["inherit_base"])
            inherit_domain = self.extractor.req_bool(ui_render_dict, ["inherit_domain"])
            raw_resolvers = self.extractor.req_list(ui_render_dict, ["resolvers"])

            resolvers: list[KBStateResolver] = []
            for r_dict in raw_resolvers:
                res_type = self.extractor.req_str(r_dict, ["type"])
                anchor = self.extractor.req_str(r_dict, ["id"])

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

    def _get_btn_map(self, sys_cfg):
        # if we dont get them, complain! 
        btn_map: dict[str, Button] = {}
        for key_char in self.extractor.req_str(sys_cfg.data, ["button_rows", "prompts_row"]):
            btn_map[key_char] = Button(type=Button.TYPE_PROMPT, key=key_char, inhabitant=None)
        for key_char in self.extractor.req_str(sys_cfg.data, ["button_rows", "shared_domains_row"]),:
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=None)
        for key_char in self.extractor.req_str(sys_cfg.data, ["button_rows", "pud_domains_row"]):
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=None)
        return btn_map