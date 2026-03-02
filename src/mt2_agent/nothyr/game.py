from ..game_interface import GameInterface
from ..game_input import GameInputs
from ..game_ui import GameUI

from .input import NothyrKeys
from .ui import NothyrUI


class Nothyr(GameInterface):
    SERVER = "Nothyr"
    WINDOW_CLASS_NAME = "eter - "
    WINDOW_NAME = "Nothyr"

    keys: GameInputs
    ui: GameUI

    def __init__(self, args, input_overrides):
        super().__init__(args, input_overrides)

        self.inputs = NothyrKeys()
        self.ui = NothyrUI()
