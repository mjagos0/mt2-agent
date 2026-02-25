from .nothyr_ui import NothyrUI

import interception
import time

ESCAPE = "esc"
OPEN_BIOLOG_KEY = "f7"

class NothyrActions:
    def __init__(self, to_screen: callable, dimensions: tuple[int, int]):
        self.ui = NothyrUI(*dimensions)
        self.to_screen = to_screen

    def open_biolog(self):
        interception.press(OPEN_BIOLOG_KEY)
        time.sleep(1)
        interception.move_to(self.to_screen(*self.ui.biolog_shop))
        time.sleep(1)
        interception.click(button="left")
        time.sleep(1)
        interception.move_to(self.to_screen(*self.ui.orc_tooth))
        time.sleep(1)
        interception.press(ESCAPE)
        time.sleep(1)
        interception.move_to(self.to_screen(*self.ui.biolog_confirm))
        time.sleep(1)
        interception.click(button="left")
        time.sleep(1)
        interception.press(ESCAPE)
