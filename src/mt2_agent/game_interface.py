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

    def cast_spell(self, hotkey: str) -> Generator[GameAction, None, None]:
        yield act.HoldKey(self.keys.CTRL)
        yield act.PressKey(self.keys.H)
        yield act.ReleaseKey(self.keys.CTRL)
        yield act.PressKey(hotkey) # TODO: Should also handle spells on 1,2,3,4 (try_to_int?)
        yield act.HoldKey(self.keys.CTRL)
        yield act.PressKey(self.keys.H)
        yield act.ReleaseKey(self.keys.CTRL)

    def use_hotkey(self, hotkey: str) -> Generator[GameAction, None, None]:
        yield act.PressKey(hotkey) # TODO: Should also handle consumables on f1,f2,f3,f4

    def check_spell_active(self, hotkey: str) -> Generator[GameAction, None, None]:
        yield act.CompareImage(self.ui.HOTKEY_F2, self.icons.sura.weaponry.enchanted_blade.base_path) # TODO
