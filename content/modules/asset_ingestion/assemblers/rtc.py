from stdlib import Any
from ...asset_ingestion import ErrorCollector, ValueExtractor
from core import ClankerAssets, PudAssets, Button, Domain

class RtcAssembler:
    def assemble(
        self,
        sys_cfg: dict[str, Any],
        shared_doms: list[Domain],
        pud_doms: list[Domain],
        collector: ErrorCollector,
    ) -> dict[str, Button]:
        extractor = ValueExtractor()
        self.collector = collector
        self.btn_map: dict[str, Button] = {}

        self._populate_domain_buttons(
            row_keys=extractor.req_str(sys_cfg, ["button_rows", "shared_domains_row"]),
            domains=shared_doms,
            sys_cfg_name="shared_domains_row",
            cfg_filename=ClankerAssets.Configs.shared_cfg,
        )

        self._populate_domain_buttons(
            row_keys=extractor.req_str(sys_cfg, ["button_rows", "pud_domains_row"]),
            domains=pud_doms,
            sys_cfg_name="pud_domains_row",
            cfg_filename=PudAssets.Configs.PUD,
        )

        for key_char in extractor.req_str(sys_cfg, ["button_rows", "prompts_row"]):
            self.btn_map[key_char] = Button(type=Button.TYPE_PROMPT, key=key_char, inhabitant=None)

        return self.btn_map

    def _populate_domain_buttons(
        self,
        row_keys: str,
        domains: list[Domain],
        sys_cfg_name: str,
        cfg_filename: str,
    ) -> None:
        dom_btns = list(row_keys)
        if len(domains) > len(dom_btns):
            overflow_cnt = len(domains) - len(dom_btns)
            domain_names = [d.name for d in domains]
            overflowing = ", ".join(domain_names[-overflow_cnt:])
            msg = (
                f"Domain overflow in '{cfg_filename}' ({sys_cfg_name}): "
                f"{overflow_cnt} domain(s) overflowed key slots '{row_keys}'. "
                f"Excess domains: [{overflowing}]"
            )
            self.collector.add_complaint(msg)

        for key_char, dom in zip(dom_btns, domains):
            self.btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=dom)
        for key_char in dom_btns[len(domains):]:
            self.btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=None)