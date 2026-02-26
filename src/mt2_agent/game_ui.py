from dataclasses import dataclass
from .game_elements import GamePt, GameRec, NAMED_ANCHORS

@dataclass
class GameUI:
    HOTKEY_F2 = GameRec(NAMED_ANCHORS["bottom-center"], (88.5, -33), (30, 30))

    BIOLOG_SHOP: GamePt = None
    BIOLOG_CONFIRM: GamePt = None
    BIOLOG_ORC_TOOTH: GamePt = None
