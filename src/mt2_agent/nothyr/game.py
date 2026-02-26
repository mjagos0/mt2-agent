from ..game_interface import GameInterface
from .. import game_actions as act
from ..game_keys import GameKeys

from .keys import NothyrKeys
from .ui import NothyrUI

class Nothyr(GameInterface):
    SERVER = "Nothyr"
    WINDOW_CLASS_NAME = "eter - "
    WINDOW_NAME = "Nothyr"
    
    def __init__(self):
        super().__init__()
        self.keys: GameKeys = NothyrKeys()
        self.ui = NothyrUI()
        
    def biolog(self):
        yield act.PressKey(self.keys.OPEN_BIOLOG_KEY)
        yield act.MoveCursor(self.ui.BIOLOG_SHOP)
        yield act.LeftClick()
        yield act.MoveCursor(self.ui.BIOLOG_ORC_TOOTH)
        yield act.PressKey(self.keys.ESCAPE)
        yield act.MoveCursor(self.ui.BIOLOG_CONFIRM)
        yield act.LeftClick()
        yield act.PressKey(self.keys.ESCAPE)
        