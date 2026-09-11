from content.config_assembly_system.translation_system.config_dtos import ConfigTranslator
from models import Button, RuntimeConfig, Keyboard
class RuntimeConfigBuilder:
    def __init__(
        self,
        pud_cfg: dict,
        sys_cfg: dict,
        shared_cfg: dict,
    ) -> None:
        self.pud_cfg = pud_cfg
        self.sys_cfg = sys_cfg
        self.shared_cfg = shared_cfg
        self.collector = ErrorCollector()
        self.translator = ConfigTranslator(self.collector)

    def build(self) -> RuntimeConfig:
        self._handle_named_filesets()
        base_resolvers = self.translator.get_resolvers(self.shared_cfg)
        self._handle_domains()
        ui_render, button_map = self._handle_buttons()

        return self.collector, RuntimeConfig(
            keyboard=Keyboard(button_map=button_map, selected_key=None),
            ui_render=ui_render,
            base_resolvers=base_resolvers,
        )

    def _handle_named_filesets(self) -> None:
        shared_map = self.translator.extract_filesets(self.shared_cfg)
        pud_map = self.translator.extract_filesets(self.pud_cfg)
        merged_map = shared_map.merge(pud_map)
        self.translator.set_filesetmap(merged_map)

    def _handle_domains(self) -> None:
        self.shared_domains = self.translator.extract_domains(self.shared_cfg)
        self.pud_domains = self.translator.extract_domains(self.pud_cfg)

    def _handle_buttons(self) -> tuple[Render, dict[str, Button]]:
        ui_render, self.kb_spec = self.translator.process_sys_cfg(self.sys_cfg)
        button_map = self._create_btn_map()
        return ui_render, button_map

    def _create_btn_map(self) -> dict[str, Button]:
        btn_map: dict[str, Button] = {}
        if not self.kb_spec:
            return btn_map

        shr_dom_btns = list(self.kb_spec.shared_domain_keys)
        if len(self.shared_domains) > len(shr_dom_btns):
            self.collector.add_complaint("More shared domains configured than available key slots")
        for key_char, dom in zip(shr_dom_btns, self.shared_domains):
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=dom)
        for key_char in shr_dom_btns[len(self.shared_domains):]:
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=None)

        pud_dom_btns = list(self.kb_spec.pud_domain_keys)
        if len(self.pud_domains) > len(pud_dom_btns):
            self.collector.add_complaint("More PUD domains configured than available key slots")
        for key_char, dom in zip(pud_dom_btns, self.pud_domains):
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=dom)
        for key_char in pud_dom_btns[len(self.pud_domains):]:
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=None)

        for key_char in self.kb_spec.prompt_keys:
            btn_map[key_char] = Button(type=Button.TYPE_PROMPT, key=key_char, inhabitant=None)

        return btn_map

class ErrorCollector:
    def __init__(self) -> None:
        self._path_stack: list[str] = []
        self._complaints: list[str] = []

    def push_path(self, segment: str) -> None:
        self._path_stack.append(segment)

    def pop_path(self) -> None:
        if self._path_stack:
            self._path_stack.pop()

    def add_complaint(self, message: str) -> None:
        active_path = " -> ".join(self._path_stack)
        if active_path:
            self._complaints.append(f"[{active_path}] {message}")
        else:
            self._complaints.append(message)

    def raise_if_any(self) -> None:
        if self._complaints:
            formatted = "\n".join(f"  - {c}" for c in self._complaints)
            raise ConfigAssemblyFailure(f"Configuration errors encounterd:\n{formatted}")