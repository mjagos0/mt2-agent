from dataclasses import dataclass
from ..game_input import GameInputs, Input, KeyboardInput


@dataclass
class NothyrKeys(GameInputs):
    DROP_METIN_QUEUE: Input = Input(keyboard=KeyboardInput("space"))
    OPEN_BIOLOG_KEY: Input = Input(keyboard=KeyboardInput("f7"))
