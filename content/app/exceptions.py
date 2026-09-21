from stdlib import traceback, ABC, abstractmethod, Any

class ExceptionPolicy:
    @classmethod
    def protect_adapter(cls, adapter: Any) -> Any:
        def _wrap(fn):
            def wrapper(*args, **kwargs):
                try:
                    return fn(*args, **kwargs)
                except BaseEx:
                    raise
                except Exception as ex:
                    raise AdapterLeakage from ex
            return wrapper

        wrapped = {
            name: _wrap(getattr(adapter, name))
            for name in dir(adapter)
            if not name.startswith("_") and callable(getattr(adapter, name))
        }

        for name, fn in wrapped.items():
            setattr(adapter, name, fn)

        return adapter

    @classmethod
    def interpret_as_fatal(cls, ex: Exception) -> str:
        if isinstance(ex, Fatal):
            fatal_ex = ex
        elif isinstance(ex, Notice):
            fatal_ex = MissedNotice()
            fatal_ex.__cause__ = ex
        else:
            fatal_ex = UnexpectedEx()
            fatal_ex.__cause__ = ex

        msg_parts = [f"\n[FATAL] {type(fatal_ex).__name__}{fatal_ex}\n"]

        cause = getattr(fatal_ex, "__cause__", None)
        if cause is not None:
            msg_parts.append("\n--- Underlying Stack Trace ---\n")
            msg_parts.append("".join(traceback.format_exception(type(cause), cause, cause.__traceback__)))
        elif fatal_ex.__traceback__ is not None:
            msg_parts.append("".join(traceback.format_exception(type(fatal_ex), fatal_ex, fatal_ex.__traceback__)))

        return "".join(msg_parts)

class BaseEx(ABC, Exception):
    def __init__(self, *args, **kwargs) -> None:
        if args or kwargs:
            details = ValueError(f"'{self.__class__.__name__}' took args={args!r}, kwargs={kwargs!r}")
            ex = IllegalExArgs()
            ex.__cause__ = details
            raise ex
        super().__init__()

    @property
    @abstractmethod
    def leaf_ex(self) -> bool: pass

class Fatal(BaseEx): pass
class Notice(BaseEx): pass

class IllegalExArgs(Fatal): leaf_ex = True
class MissedNotice(Fatal): leaf_ex = True
class AdapterLeakage(Fatal): leaf_ex = True
class UnexpectedEx(Fatal): leaf_ex = True
class CorruptClanker(Fatal): leaf_ex = True
class ConfigAssembly(Fatal): leaf_ex = True
class TestSequenceEnded(Fatal): leaf_ex = True
class IllegalDuplicateFile(Fatal): leaf_ex = True
class UserTask(Fatal): leaf_ex = True
class WorkspaceAlreadyInitialized(Fatal): leaf_ex = True
class UserDecline(Notice): leaf_ex = True
class ProgramExit(Notice): leaf_ex = True
class NoConfig(Notice): leaf_ex = True
class HotPromptRequested(Notice): leaf_ex = True