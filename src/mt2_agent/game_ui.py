from dataclasses import dataclass

NAMED_ANCHORS = {
    "top-left": (0.0, 0.0),
    "top-right": (1.0, 0.0),
    "bottom-left": (0.0, 1.0),
    "bottom-right": (1.0, 1.0),
    "center": (0.5, 0.5),
    "bottom-center": (0.5, 1.0),
    "top-center": (0.5, 0.0),
}


@dataclass(frozen=True)
class GamePt:
    anchor: tuple[float, float]
    offset: tuple[float, float]

    @property
    def widthAnchor(self) -> float:
        return self.anchor[0]

    @property
    def heightAnchor(self) -> float:
        return self.anchor[1]

    @property
    def widthOffset(self) -> float:
        return self.offset[0]

    @property
    def heightOffset(self) -> float:
        return self.offset[1]


@dataclass(frozen=True)
class GameRectangle(GamePt):
    dimensions: tuple[int, int] = (0, 0)

    @property
    def width(self) -> float:
        return self.dimensions[0]

    @property
    def height(self) -> float:
        return self.dimensions[1]


# Shared constants
_BC = NAMED_ANCHORS["bottom-center"]
_C = NAMED_ANCHORS["center"]
_TR = NAMED_ANCHORS["top-right"]
_BR = NAMED_ANCHORS["bottom-right"]


@dataclass
class GameUI:
    # Spells
    HOTKEY_1: GameRectangle = GameRectangle(_BC, (11, -33), (30, 30))
    HOTKEY_2: GameRectangle = GameRectangle(_BC, (-21, -33), (30, 30))
    HOTKEY_3: GameRectangle = GameRectangle(_BC, (-53, -33), (30, 30))
    HOTKEY_4: GameRectangle = GameRectangle(_BC, (-85, -33), (30, 30))

    HOTKEY_F1: GameRectangle = GameRectangle(_BC, (57, -33), (30, 30))
    HOTKEY_F2: GameRectangle = GameRectangle(_BC, (89, -33), (30, 30))
    HOTKEY_F3: GameRectangle = GameRectangle(_BC, (121, -33), (30, 30))
    HOTKEY_F4: GameRectangle = GameRectangle(_BC, (153, -33), (30, 30))

    # Stuck detection
    COORDINATES: GameRectangle = GameRectangle(_TR, (-99, 180), (65, 15))

    # Captcha
    CAPTCHA_DETECT: GameRectangle = GameRectangle(_C, (-155, -133), (307, 46))
    CAPTCHA_PROMPT: GameRectangle = GameRectangle(_C, (-90.5, -85.5), (181, 13))
    CAPTCHA_CHALLENGE: GameRectangle = GameRectangle(_C, (-132.5, -26.5), (264, 132))
    CAPTCHA_TARGET: GameRectangle = GameRectangle(_C, (82.5, 56.5), (33, 34))

    # Login
    LOGIN_DETECT: GameRectangle = GameRectangle(_C, (-72.5, 165), (146, 50))
    LOGIN_CH3: GamePt = GamePt(_C, (144.5, -5))

    # Respawn
    RESPAWN_DETECT: GameRectangle = GameRectangle(NAMED_ANCHORS["top-left"], (52, 59), (195, 40))
    
    # Biolog
    BIOLOG_SHOP: GamePt = GamePt(_C, (102, -69.5))
    BIOLOG_CONFIRM: GamePt = GamePt(_C, (15.5, -114.5))
    BIOLOG_OK: GamePt = GamePt(_C, (1.5, 20))

    # Row 0
    BIOLOG_0_0 = GamePt(_BR, (-353.5, -552.5))
    BIOLOG_1_0 = GamePt(_BR, (-321.5, -552.5))
    BIOLOG_2_0 = GamePt(_BR, (-289.5, -552.5))
    BIOLOG_3_0 = GamePt(_BR, (-257.5, -552.5))
    BIOLOG_4_0 = GamePt(_BR, (-225.5, -552.5))

    # Row 1
    BIOLOG_0_1 = GamePt(_BR, (-353.5, -520.5))
    BIOLOG_1_1 = GamePt(_BR, (-321.5, -520.5))
    BIOLOG_2_1 = GamePt(_BR, (-289.5, -520.5))
    BIOLOG_3_1 = GamePt(_BR, (-257.5, -520.5))
    BIOLOG_4_1 = GamePt(_BR, (-225.5, -520.5))

    # Row 2
    BIOLOG_0_2 = GamePt(_BR, (-353.5, -488.5))
    BIOLOG_1_2 = GamePt(_BR, (-321.5, -488.5))
    BIOLOG_2_2 = GamePt(_BR, (-289.5, -488.5))
    BIOLOG_3_2 = GamePt(_BR, (-257.5, -488.5))
    BIOLOG_4_2 = GamePt(_BR, (-225.5, -488.5))

    @property
    def biolog_items(self) -> list[GamePt]:
        return [
            self.BIOLOG_0_0, self.BIOLOG_1_0, self.BIOLOG_2_0, self.BIOLOG_3_0, self.BIOLOG_4_0,
            self.BIOLOG_0_1, self.BIOLOG_1_1, self.BIOLOG_2_1, self.BIOLOG_3_1, self.BIOLOG_4_1,
            self.BIOLOG_0_2, self.BIOLOG_1_2, self.BIOLOG_2_2, self.BIOLOG_3_2, self.BIOLOG_4_2,
        ]

    @property
    def n_hotkeys(self) -> list[GameRectangle]:
        return [self.HOTKEY_1, self.HOTKEY_2, self.HOTKEY_3, self.HOTKEY_4]

    @property
    def f_hotkeys(self) -> list[GameRectangle]:
        return [self.HOTKEY_F1, self.HOTKEY_F2, self.HOTKEY_F3, self.HOTKEY_F4]

    @property
    def all_hotkeys(self) -> list[GameRectangle]:
        return self.f_hotkeys + self.n_hotkeys
