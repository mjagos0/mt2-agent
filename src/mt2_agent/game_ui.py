from .game_elements import GamePt, GameRec, NAMED_ANCHORS

class GameUI:
    HOTKEY_1 = GameRec(NAMED_ANCHORS["bottom-center"], (11, -33), (30, 30))
    HOTKEY_2 = GameRec(NAMED_ANCHORS["bottom-center"], (-21, -33), (30, 30))
    HOTKEY_3 = GameRec(NAMED_ANCHORS["bottom-center"], (-53, -33), (30, 30))
    HOTKEY_4 = GameRec(NAMED_ANCHORS["bottom-center"], (-85, -33), (30, 30))

    HOTKEY_F1 = GameRec(NAMED_ANCHORS["bottom-center"], (57, -33), (30, 30))
    HOTKEY_F2 = GameRec(NAMED_ANCHORS["bottom-center"], (89, -33), (30, 30))
    HOTKEY_F3 = GameRec(NAMED_ANCHORS["bottom-center"], (121, -33), (30, 30))
    HOTKEY_F4 = GameRec(NAMED_ANCHORS["bottom-center"], (153, -33), (30, 30))

    COORDINATES = GameRec(anchor=NAMED_ANCHORS["top-right"], offset=(-99, 180), dimensions=(65, 15))
    
    BIOLOG_SHOP: GamePt
    BIOLOG_CONFIRM: GamePt
    BIOLOG_ORC_TOOTH: GamePt

    


    N_HOTKEYS = [HOTKEY_1, HOTKEY_2, HOTKEY_3, HOTKEY_4]
    F_HOTKEYS = [HOTKEY_F1, HOTKEY_F2, HOTKEY_F3, HOTKEY_F4]
    ALL_HOTKEYS = F_HOTKEYS + N_HOTKEYS
