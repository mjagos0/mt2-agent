from ..game_interface import GameInterface
from ..game_input import GameInputs, Input
from ..game_ui import GameUI

from .input import NothyrKeys
from .ui import NothyrUI

import argparse

class Nothyr(GameInterface):
    SERVER = "Nothyr"
    WINDOW_CLASS_NAME = "eter - "
    WINDOW_NAME = "Nothyr"
    SERVER_ASSETS = "nothyr"

    keys: GameInputs
    ui: GameUI

    def __init__(self, args: argparse.Namespace, input_overrides: dict[str, Input]):
        super().__init__(args, input_overrides)

        self.inputs = NothyrKeys()
        self.ui = NothyrUI()
