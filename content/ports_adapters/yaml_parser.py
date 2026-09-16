from ruamel.yaml import YAML
from ports_adapters.ports import ConfigParserPort

class RuamelYamlParserAdapter(ConfigParserPort):
    def __init__(self) -> None:
        self.yaml = YAML()
    def get_as_dict(self, raw_text: str) -> dict:
        return self.yaml.load(raw_text)