from abc import ABC, abstractmethod
from app.entities import Button

class KBService(ABC):
    @abstractmethod
    def set_button_map(self, button_map: dict[str, Button]) -> None: ...