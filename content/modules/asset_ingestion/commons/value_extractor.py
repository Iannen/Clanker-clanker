from stdlib import Any
from core import ConfigAssembly

class NotFound(Exception): pass 
class WrongType(Exception): pass 

class ValueExtractor:
    def valid_args(self, frame_locals: dict) -> bool:
        return all(v is not None for k, v in frame_locals.items() if k != "self")

    def _req(
        self, data: Any, path: list[str], target_type: type | tuple[type, ...], default: Any = None
    ) -> Any:
        curr = data
        path_str = " -> ".join(path)
        try:
            for k in path:
                curr = curr[k]
        except (KeyError, TypeError, IndexError):
            if default is not None:
                return default
            raise ConfigAssembly(f"Missing required config path: '{path_str}'")

        if not isinstance(curr, target_type) or (
            str in (target_type if isinstance(target_type, tuple) else (target_type,))
            and isinstance(curr, bool)
        ):
            expected_name = (
                " or ".join(t.__name__ for t in target_type)
                if isinstance(target_type, tuple)
                else target_type.__name__
            )
            raise ConfigAssembly(
                f"Type mismatch at path '{path_str}': expected {expected_name}, got {type(curr).__name__}"
            )
        return curr

    def req_str(self, data: Any, path: list[str]) -> str:
        return self._req(data, path, str)

    def req_dict(self, data: Any, path: list[str]) -> dict[str, Any]:
        return self._req(data, path, dict)

    def req_list(self, data: Any, path: list[str]) -> list[Any]:
        return self._req(data, path, list)

    def req_bool(self, data: Any, path: list[str]) -> bool:
        return self._req(data, path, bool)

    def req_int(self, data: Any, path: list[str]) -> int:
        return self._req(data, path, int)

    def req_str_or_dict(self, data: Any, path: list[str]) -> str | dict[str, Any]:
        return self._req(data, path, (str, dict))

    def opt_str(self, data: Any, path: list[str], default: str | None = None) -> str | None:
        return self._req(data, path, str, default=default)

    def opt_dict(
        self, data: Any, path: list[str], default: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        return self._req(data, path, dict, default=default)

    def opt_list(
        self, data: Any, path: list[str], default: list[Any] | None = None
    ) -> list[Any] | None:
        return self._req(data, path, list, default=default)

    def opt_bool(
        self, data: Any, path: list[str], default: bool | None = None
    ) -> bool | None:
        return self._req(data, path, bool, default=default)

    def opt_int(
        self, data: Any, path: list[str], default: int | None = None
    ) -> int | None:
        return self._req(data, path, int, default=default)

    def opt_str_or_dict(
        self, data: Any, path: list[str], default: str | dict[str, Any] | None = None
    ) -> str | dict[str, Any] | None:
        return self._req(data, path, (str, dict), default=default)
