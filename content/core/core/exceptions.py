from stdlib import ABC, abstractmethod

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
class IllegalDuplicateFile(Fatal): leaf_ex = True
class UserTask(Fatal): leaf_ex = True
class WorkspaceAlreadyInitialized(Fatal): leaf_ex = True
class UserDecline(Notice): leaf_ex = True
class ProgramExit(Notice): leaf_ex = True
class NoConfig(Notice): leaf_ex = True
class HotPromptRequested(Notice): leaf_ex = True