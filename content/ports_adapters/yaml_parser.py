from ruamel.yaml import YAML
from ports_adapters.ports import ConfigParserPort, ConfigParseError

class RuamelYamlParserAdapter(ConfigParserPort):
    def __init__(self) -> None:
        self.yaml = YAML()
    def get_as_dict(self, raw_text: str) -> dict:
        try:
            return self.yaml.load(raw_text)
        except Exception as ex: raise ConfigParseError from ex
        