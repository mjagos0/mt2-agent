from .game_elements import GamePt, GameRec, NAMED_ANCHORS

class GameUI:
    HOTKEY_F2 = GameRec(NAMED_ANCHORS["bottom-center"], (88.5, -33), (30, 30))

    BIOLOG_SHOP: GamePt
    BIOLOG_CONFIRM: GamePt
    BIOLOG_ORC_TOOTH: GamePt
