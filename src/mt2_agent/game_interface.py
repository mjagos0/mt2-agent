from . import game_actions as act
from .game_keys import GameKeys
from .game_ui import GameUI
from .game_icons import GameIcons
from .game_actions import GameAction

from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import Any


class GameInterface(ABC):
    SERVER: str
    WINDOW_CLASS_NAME: str
    WINDOW_NAME: str

    def __init__(self):
        self.keys = GameKeys()
        self.ui = GameUI()
        self.icons = GameIcons()

    def __init_subclass__(cls, **kwargs: Any):
        super().__init_subclass__(**kwargs)
        required = ('SERVER', 'WINDOW_CLASS_NAME')
        missing = [attr for attr in required if not hasattr(cls, attr)]
        if missing:
            raise TypeError(f"{cls.__name__} must define: {', '.join(missing)}")

    @abstractmethod
    def biolog(self) -> Generator[GameAction, None, None]:
        ...

    def try_cast_spells(self) -> Generator[GameAction, None, None]:
        yield act.TryCastSpell(self.ui.HOTKEY_1, self.keys.HOTKEY_1)
        yield act.TryCastSpell(self.ui.HOTKEY_2, self.keys.HOTKEY_2)
        yield act.TryCastSpell(self.ui.HOTKEY_3, self.keys.HOTKEY_3)
        yield act.TryCastSpell(self.ui.HOTKEY_4, self.keys.HOTKEY_4)

        yield act.TryCastSpell(self.ui.HOTKEY_F1, self.keys.HOTKEY_F1)
        yield act.TryCastSpell(self.ui.HOTKEY_F2, self.keys.HOTKEY_F2)
        yield act.TryCastSpell(self.ui.HOTKEY_F3, self.keys.HOTKEY_F3)
        yield act.TryCastSpell(self.ui.HOTKEY_F4, self.keys.HOTKEY_F4)

    def bravery_cape(self) -> Generator[GameAction, None, None]:
        yield act.PressKey(self.keys.HOTKEY_1)

    def pickup_items(self) -> Generator[GameAction, None, None]:
        yield act.PressKey(self.keys.PICKUP_ITEMS)

    def stuck_detection(self) -> Generator[GameAction, None, None]:
        yield act.StuckDetection(self.ui.COORDINATES)