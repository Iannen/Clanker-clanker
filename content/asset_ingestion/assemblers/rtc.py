from dataclasses import dataclass
from typing import Any
from asset_ingestion.commons.error_collector import ErrorCollector
from asset_ingestion.commons.fileset_map import FilesetMap
from asset_ingestion.commons.value_extractor import ValueExtractor
from asset_ingestion.extractors.domains import DomainsExtractor
from app.constants import CfgFragments
from app.entities import Button, Keyboard

@dataclass
class DomainOverflow: # create general complain based on 'enum' ?
    sys_cfg_name: str
    row_keys: str
    domain_names: list[str]
    cfg_filename: str
    overflow_count: int

    def get_msg(self) -> str:
        overflowing = ", ".join(self.domain_names[-self.overflow_count:])
        return (
            f"Domain overflow in '{self.cfg_filename}' ({self.sys_cfg_name}): "
            f"{self.overflow_count} domain(s) overflowed key slots '{self.row_keys}'. "
            f"Excess domains: [{overflowing}]"
        )


    
class RtcAssembler:
    def assemble(
        self,
        sys_cfg: dict[str, Any],
        shared_doms: list[Domain],
        pud_doms: list[Domain],
        collector: ErrorCollector,
    ) -> Keyboard:
        extractor = ValueExtractor()
        self.collector = collector
        self.btn_map: dict[str, Button] = {}

        self._populate_domain_buttons(
            row_keys=extractor.req_str(sys_cfg, ["button_rows", "shared_domains_row"]),
            domains=shared_doms,
            sys_cfg_name="shared_domains_row",
            cfg_filename=CfgFragments.SHARED_CFG,
        )

        self._populate_domain_buttons(
            row_keys=extractor.req_str(sys_cfg, ["button_rows", "pud_domains_row"]),
            domains=pud_doms,
            sys_cfg_name="pud_domains_row",
            cfg_filename=CfgFragments.PUD_CFG,
        )

        for key_char in extractor.req_str(sys_cfg, ["button_rows", "prompts_row"]):
            self.btn_map[key_char] = Button(type=Button.TYPE_PROMPT, key=key_char, inhabitant=None)

        return Keyboard(button_map=self.btn_map, selected_key=None)

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
            dof = DomainOverflow(
                sys_cfg_name=sys_cfg_name,
                row_keys=row_keys,
                domain_names=[d.name for d in domains],
                cfg_filename=cfg_filename,
                overflow_count=overflow_cnt,
            )
            self.collector.record_domain_overflow(dof)

        for key_char, dom in zip(dom_btns, domains):
            self.btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=dom)
        for key_char in dom_btns[len(domains):]:
            self.btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=None)