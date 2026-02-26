from .game_elements import GamePt, GameRec

from dataclasses import dataclass
from pathlib import Path

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
class CompareImage:
    region: GameRec
    reference: Path  # path to reference image

# Union type for type checking
GameAction = PressKey | HoldKey | ReleaseKey | MoveCursor | LeftClick | RightClick | CompareImage