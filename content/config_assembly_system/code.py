from config_assembly_system.translation_system.config_dtos import ConfigTranslator, ErrorCollector
from contracts.assembly_system_contract import RtcAssembler, Report
from models import Button, RuntimeConfig, Keyboard, ConfigAssemblyFailure
from dataclasses import dataclass

class RuntimeConfigAssembler(RtcAssembler):
    def assemble(self, sys_cfg: dict, pud_cfg: dict, shared_cfg: dict) -> tuple[Report, RuntimeConfig]:
        collector = ErrorCollector()
        ctx = Ctx(sys_cfg, pud_cfg, shared_cfg, collector, ConfigTranslator(collector))

        self._handle_named_filesets(ctx)
        base_resolvers = ctx.translator.get_resolvers(ctx.shared_cfg)
        self._handle_domains(ctx)
        ui_render, button_map = self._handle_buttons(ctx)

        return ctx.collector, RuntimeConfig(
            keyboard=Keyboard(button_map=button_map, selected_key=None),
            ui_render=ui_render,
            base_resolvers=base_resolvers,
        )

    def _handle_named_filesets(self, ctx: Ctx) -> None:
        shared_map = ctx.translator.extract_filesets(ctx.shared_cfg)
        pud_map = ctx.translator.extract_filesets(ctx.pud_cfg)
        merged_map = shared_map.merge(pud_map)
        ctx.translator.set_filesetmap(merged_map)

    def _handle_domains(self, ctx: Ctx) -> None:
        ctx.shared_doms = ctx.translator.extract_domains(ctx.shared_cfg)
        ctx.pud_doms = ctx.translator.extract_domains(ctx.pud_cfg)

    def _handle_buttons(self, ctx: Ctx) -> tuple[Render, dict[str, Button]]:
        ui_render, ctx.kb_spec = ctx.translator.process_sys_cfg(ctx.sys_cfg)
        button_map = self._create_btn_map(ctx)
        return ui_render, button_map

    def _create_btn_map(self, ctx: Ctx) -> dict[str, Button]:
        btn_map: dict[str, Button] = {}
        if not ctx.kb_spec:
            return btn_map

        shr_dom_btns = list(ctx.kb_spec.shared_domain_keys)
        if len(ctx.shared_doms) > len(shr_dom_btns):
            ctx.collector.add_complaint("More shared domains configured than available key slots")
        for key_char, dom in zip(shr_dom_btns, ctx.shared_doms):
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=dom)
        for key_char in shr_dom_btns[len(ctx.shared_doms):]:
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=None)

        pud_dom_btns = list(ctx.kb_spec.pud_domain_keys)
        if len(ctx.pud_doms) > len(pud_dom_btns):
            ctx.collector.add_complaint("More PUD domains configured than available key slots")
        for key_char, dom in zip(pud_dom_btns, ctx.pud_doms):
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=dom)
        for key_char in pud_dom_btns[len(ctx.pud_doms):]:
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=None)

        for key_char in ctx.kb_spec.prompt_keys:
            btn_map[key_char] = Button(type=Button.TYPE_PROMPT, key=key_char, inhabitant=None)

        return btn_map

    def assert_no_quotes(self, raw_text: str, filepath: str = "") -> None:
        """ i just stuck this here to not lose sight of it, its refugee from old 'ConfigValidator' which has been decomissioned"""
        violations = []
        for idx, line in enumerate(raw_text.splitlines(), start=1):
            if "'" in line:
                parts = line.split("'")
                if len(parts) == 3:
                    content = parts[1]
                    is_digits = content.isdigit()
                    has_double_quote = '"' in content
                    if not (is_digits or has_double_quote):
                        violations.append(f"    line {idx} has quotes: {line}")
                else:
                    violations.append(f"    line {idx} has quotes: {line}")
            elif '"' in line:
                violations.append(f"    line {idx} has quotes: {line}")
                
        if violations:
            msg_parts = [filepath] if filepath else []
            msg_parts.extend(violations)
            raise ConfigViolations("\n".join(msg_parts))

@dataclass
class Ctx:
    sys_cfg: dict
    pud_cfg: dict
    shared_cfg: dict
    collector: ErrorCollector
    translator: ConfigTranslator
    shared_doms: list[Domain] | None = None
    pud_doms: list[Domain] | None = None
    kb_spec: KbSpec | None = None
