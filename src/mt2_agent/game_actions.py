from dataclasses import dataclass
from .game_elements import GamePt, GameRec

@dataclass
class PressKey:
    key: str

@dataclass
class HoldKey:
    key: str

@dataclass
class ReleaseKey:
    key: str

@dataclass
class MoveCursor:
    target: GamePt

@dataclass
class LeftClick:
    ...

@dataclass
class RightClick:
    ...

@dataclass
class CaptureRegion:
    region: GameRec

@dataclass
class CompareImage:
    region: GameRec
    reference: str  # path to reference image

# Union type for type checking
Action = PressKey | MoveCursor | CaptureRegion | CompareImage