from ..game_elements import GamePt, GameRec, NAMED_ANCHORS
from ..game_ui import GameUI

class NothyrUI(GameUI):
    BIOLOG_SHOP = GamePt(NAMED_ANCHORS["center"], (102, -69.5))
    BIOLOG_CONFIRM = GamePt(NAMED_ANCHORS["center"], (15.5, -114.5))
    BIOLOG_ORC_TOOTH = GamePt((2/3, 0.0), (196.33, 249))
