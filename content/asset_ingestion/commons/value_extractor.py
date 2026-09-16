# fix imports pls
class ValueExtractor:
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

    def req_str(self, data: Any, path: list[str], default: Any = None) -> str:
        return self._req(data, path, str, default)

    def req_dict(self, data: Any, path: list[str], default: Any = None) -> dict[str, Any]:
        return self._req(data, path, dict, default)

    def req_list(self, data: Any, path: list[str], default: Any = None) -> list[Any]:
        return self._req(data, path, list, default)

    def req_bool(self, data: Any, path: list[str], default: Any = None) -> bool:
        return self._req(data, path, bool, default)

    def req_int(self, data: Any, path: list[str], default: Any = None) -> int:
        return self._req(data, path, int, default)

    def req_str_or_dict(self, data: Any, path: list[str], default: Any = None) -> str | dict[str, Any]:
        return self._req(data, path, (str, dict), default)