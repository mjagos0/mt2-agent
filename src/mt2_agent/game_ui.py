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


@dataclass
class GameUI:
    HOTKEY_1: GameRectangle = GameRectangle(_BC, (11, -33), (30, 30))
    HOTKEY_2: GameRectangle = GameRectangle(_BC, (-21, -33), (30, 30))
    HOTKEY_3: GameRectangle = GameRectangle(_BC, (-53, -33), (30, 30))
    HOTKEY_4: GameRectangle = GameRectangle(_BC, (-85, -33), (30, 30))

    HOTKEY_F1: GameRectangle = GameRectangle(_BC, (57, -33), (30, 30))
    HOTKEY_F2: GameRectangle = GameRectangle(_BC, (89, -33), (30, 30))
    HOTKEY_F3: GameRectangle = GameRectangle(_BC, (121, -33), (30, 30))
    HOTKEY_F4: GameRectangle = GameRectangle(_BC, (153, -33), (30, 30))

    COORDINATES: GameRectangle = GameRectangle(_TR, (-99, 180), (65, 15))

    CAPTCHA_DETECT: GameRectangle = GameRectangle(_C, (-141, -127), (272, 37))
    CAPTCHA_PROMPT: GameRectangle = GameRectangle(_C, (-90.5, -85.5), (181, 13))
    CAPTCHA_CHALLENGE: GameRectangle = GameRectangle(_C, (-132.5, -26.5), (264, 132))
    CAPTCHA_TARGET: GameRectangle = GameRectangle(_C, (82.5, 56.5), (33, 34))

    # Configurable per-instance
    BIOLOG_SHOP: GamePt | None = None
    BIOLOG_CONFIRM: GamePt | None = None
    BIOLOG_ORC_TOOTH: GamePt | None = None

    @property
    def n_hotkeys(self) -> list[GameRectangle]:
        return [self.HOTKEY_1, self.HOTKEY_2, self.HOTKEY_3, self.HOTKEY_4]

    @property
    def f_hotkeys(self) -> list[GameRectangle]:
        return [self.HOTKEY_F1, self.HOTKEY_F2, self.HOTKEY_F3, self.HOTKEY_F4]

    @property
    def all_hotkeys(self) -> list[GameRectangle]:
        return self.f_hotkeys + self.n_hotkeys
