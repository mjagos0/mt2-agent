from .game_actions import (
    PressKey, HoldKey, ReleaseKey,
    MoveCursor, LeftClick, RightClick,
    CompareImage
)
from .window_manager import Window, Screenshot
from .game_elements import GamePt, GameRec

import logging
import time

import interception

logger = logging.getLogger(__name__)


class GameExecutor:
    def __init__(self, window: Window, action_delay: float = 0.3):
        self.window = window
        self.action_delay = action_delay

    def execute(self, actions):
        """Consume a generator of actions and execute each one."""
        for action in actions:
            logger.debug(f"Executing: {action}")
            self._dispatch(action)
            time.sleep(self.action_delay)

    def _dispatch(self, action):
        match action:
            case PressKey(key=key):
                self._press_key(key)
            case HoldKey(key=key):
                self._hold_key(key)
            case ReleaseKey(key=key):
                self._release_key(key)
            case MoveCursor(target=target):
                self._move_cursor(target)
            case LeftClick():
                self._left_click()
            case RightClick():
                self._right_click()
            case CompareImage(region=region, reference=reference):
                self._compare_image(region, reference)
            case _:
                raise ValueError(f"Unknown action: {action}")

    def _press_key(self, key: str):
        logger.debug(f"Press: {key}")
        interception.press(key)

    def _hold_key(self, key: str):
        logger.debug(f"Hold: {key}")
        interception.key_down(key)

    def _release_key(self, key: str):
        logger.debug(f"Release: {key}")
        interception.key_up(key)

    def _move_cursor(self, target: GamePt):
        x, y = self.window.gamept_to_screenpt(target)
        logger.indebugfo(f"Move cursor to: ({x}, {y})")
        interception.move_to(x, y)

    def _left_click(self):
        logger.debug("Left click")
        interception.click(button="left")

    def _right_click(self):
        logger.debug("Right click")
        interception.click(button="right")

    def _compare_image(self, region: GameRec, reference: str) -> bool:
        screenshot = self.window.capture(region)
        logger.info(f"Comparing region to {reference}")
        # cv2 template matching here
        return False
    