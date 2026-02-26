from ..game_interface import GameInterface
from .. import game_actions as act
from ..game_keys import GameKeys
from ..game_ui import GameUI

from .keys import NothyrKeys
from .ui import NothyrUI

class Nothyr(GameInterface):
    SERVER = "Nothyr"
    WINDOW_CLASS_NAME = "eter - s0:b4:p:6a1ed0"
    
    keys: GameKeys = NothyrKeys()
    ui = NothyrUI()
    
    def biolog(self):
        yield act.PressKey(self.keys.OPEN_BIOLOG_KEY)
        yield act.MoveCursor(self.ui.BIOLOG_SHOP)
        yield act.LeftClick()
        yield act.MoveCursor(self.ui.BIOLOG_ORC_TOOTH)
        yield act.PressKey(self.keys.ESCAPE)
        yield act.MoveCursor(self.ui.BIOLOG_CONFIRM)
        yield act.LeftClick()
        yield act.PressKey(self.keys.ESCAPE)
        



# interception.press(OPEN_BIOLOG_KEY)
# time.sleep(1)
# interception.move_to(self.to_screen(*self.ui.biolog_shop))
# time.sleep(1)
# interception.click(button="left")
# time.sleep(1)
# interception.move_to(self.to_screen(*self.ui.orc_tooth))
# time.sleep(1)
# interception.press(ESCAPE)
# time.sleep(1)
# interception.move_to(self.to_screen(*self.ui.biolog_confirm))
# time.sleep(1)
# interception.click(button="left")
# time.sleep(1)
# interception.press(ESCAPE)