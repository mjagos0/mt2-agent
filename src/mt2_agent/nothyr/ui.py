from dataclasses import dataclass
from ..game_ui import NAMED_ANCHORS, GameUI, GamePt

_C = NAMED_ANCHORS["center"]


@dataclass
class NothyrUI(GameUI):
    BIOLOG_SHOP: GamePt = GamePt(_C, (102, -69.5))
    BIOLOG_CONFIRM: GamePt = GamePt(_C, (15.5, -114.5))
    BIOLOG_ORC_TOOTH: GamePt = GamePt((2 / 3, 0.0), (196.33, 249))
