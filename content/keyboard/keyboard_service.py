from app.deps.keyboard import KBService
from app.entities import Button

class KBServiceImpl(KBService):
    def set_button_map(self, button_map: dict[str, Button]) -> None:
        self.button_map = button_map