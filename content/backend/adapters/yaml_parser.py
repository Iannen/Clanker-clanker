from ruamel.yaml import YAML
from core.engine_deps import ConfigParserPort, ConfigParseError

class RuamelYamlParserAdapter(ConfigParserPort):
    def __init__(self) -> None:
        self.yaml = YAML()
    def get_as_dict(self, raw_text: str) -> dict:
        try:
            parsed = self.yaml.load(raw_text)
            if not isinstance(parsed, dict):
                raise ConfigParseError("Parsed YAML content is not a mapping/dictionary object.")
            return dict(parsed)
        except Exception as ex:
            raise ConfigParseError(f"Failed to parse YAML config: {ex}") from ex
        