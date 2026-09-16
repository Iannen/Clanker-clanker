from abc import ABC, abstractmethod

class BaseEx(ABC, Exception):
    @property
    @abstractmethod
    def leaf_ex(self) -> bool:pass

class Fatal(BaseEx):
    def __str__(self) -> str:
        msg = super().__str__()
        return f": {msg}" if msg else ""

class Notice(BaseEx): pass

class MissedNotice(Fatal): leaf_ex = True
class NoticeArgs(Fatal):
    leaf_ex = True
    def __init__(self, cls_name: str, args: tuple, kwargs: dict):
        super().__init__(f"Notice '{cls_name}' illegal args: args={args!r}, kwargs={kwargs!r}")
class AdapterLeakage(Fatal):
    leaf_ex = True
    def __str__(self) -> str:
        if not self.args and self.__cause__:
            return f": [{type(self.__cause__).__name__}] {self.__cause__}"
        return super().__str__()
class UnexpectedEx(Fatal): leaf_ex = True
class CorruptClanker(Fatal): leaf_ex = True
class ConfigAssembly(Fatal): leaf_ex = True
class IllegalDuplicateFile(Fatal): leaf_ex = True
class UserTask(Fatal): leaf_ex = True

class UserDecline(Notice): leaf_ex = True
class ProgramExit(Notice): 
    leaf_ex = True
    MSG_DEFAULT: str = "Program exited"
    MSG_DECLINED_INIT: str = "Initialization declined by user"
    MSG_DECLINED_BOOTSTRAP: str = "Bootstrap declined by user"
    
class NoConfig(Notice): leaf_ex = True