from dataclasses import dataclass
from typing import Any
from app.models import (
    Button,
    CfgFragments,
    Domain,
    Keyboard,
    Render,
    Resolver,
)
from asset_ingestion.commons.error_collector import ErrorCollector
from asset_ingestion.commons.fileset_map import FilesetMap
from asset_ingestion.commons.kb_spec import KbSpec
from asset_ingestion.commons.value_extractor import ValueExtractor
from asset_ingestion.parsers.domain_extractor import DomainExtractor


@dataclass
class DomainOverflow:
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
    def __init__(
        self,
        sys_cfg: dict[str, Any],
        shared_doms: list[Domain],
        pud_doms: list[Domain],
        shared_cfg: dict[str, Any],
        collector: ErrorCollector,
        fileset_map: FilesetMap,
    ) -> None:
        self.sys_cfg = sys_cfg
        self.shared_doms = shared_doms
        self.pud_doms = pud_doms
        self.shared_cfg = shared_cfg
        self.collector = collector
        self.fileset_map = fileset_map
        self.extractor = ValueExtractor()

    def assemble(self) -> Keyboard:
        kb_spec = KbSpec(
            shared_domain_keys=self.extractor.req_str(self.sys_cfg, ["button_rows", "shared_domains_row"]),
            pud_domain_keys=self.extractor.req_str(self.sys_cfg, ["button_rows", "pud_domains_row"]),
            prompt_keys=self.extractor.req_str(self.sys_cfg, ["button_rows", "prompts_row"]),
        )

        button_map = self._create_btn_map(kb_spec)
        return Keyboard(button_map=button_map, selected_key=None)

    def _create_btn_map(self, kb_spec: KbSpec) -> dict[str, Button]:
        btn_map: dict[str, Button] = {}

        shr_dom_btns = list(kb_spec.shared_domain_keys)
        if len(self.shared_doms) > len(shr_dom_btns):
            overflow_cnt = len(self.shared_doms) - len(shr_dom_btns)
            dof = DomainOverflow(
                sys_cfg_name="shared_domains_row",
                row_keys=kb_spec.shared_domain_keys,
                domain_names=[d.name for d in self.shared_doms],
                cfg_filename=CfgFragments.SHARED_CFG,
                overflow_count=overflow_cnt,
            )
            self.collector.record_domain_overflow(dof)

        for key_char, dom in zip(shr_dom_btns, self.shared_doms):
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=dom)
        for key_char in shr_dom_btns[len(self.shared_doms):]:
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=None)

        pud_dom_btns = list(kb_spec.pud_domain_keys)
        if len(self.pud_doms) > len(pud_dom_btns):
            overflow_cnt = len(self.pud_doms) - len(pud_dom_btns)
            dof = DomainOverflow(
                sys_cfg_name="pud_domains_row",
                row_keys=kb_spec.pud_domain_keys,
                domain_names=[d.name for d in self.pud_doms],
                cfg_filename=CfgFragments.PUD_CFG,
                overflow_count=overflow_cnt,
            )
            self.collector.record_domain_overflow(dof)

        for key_char, dom in zip(pud_dom_btns, self.pud_doms):
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=dom)
        for key_char in pud_dom_btns[len(self.pud_doms):]:
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=None)

        for key_char in kb_spec.prompt_keys:
            btn_map[key_char] = Button(type=Button.TYPE_PROMPT, key=key_char, inhabitant=None)

        return btn_map