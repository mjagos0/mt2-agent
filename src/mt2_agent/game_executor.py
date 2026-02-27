from .game_actions import (
    PressKey, HoldKey, ReleaseKey,
    MoveCursor, LeftClick, RightClick,
    TryCastSpell
)
from .window_manager import Window
from .game_elements import GamePt, GameRec
from .game_actions import GameAction
from .util_ability_ready import is_hotkey_castable
from .util_text_detection import read_coordinates, read_text

import logging
import time
from collections.abc import Generator
from pathlib import Path

import interception

logger = logging.getLogger(__name__)


class GameExecutor:
    def __init__(self, window: Window, throttle: float):
        self.window = window
        self.throttle = throttle
        
        self.last_coordinates: tuple[int, int] = (0, 0)
        self.stagnant_frames: int = 0
        self.stagnant_threshold: int = 5

    def execute(self, actions: Generator[GameAction, None, None]) -> None:
        """Consume a generator of actions and execute each one."""
        for action in actions:
            logger.debug(f"Executing: {action}")
            self._dispatch(action)
            time.sleep(self.throttle)

    def _dispatch(self, action: GameAction) -> None:
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
            case TryCastSpell(hotkey_ui=hotkey_ui, hotkey=hotkey):
                self._try_cast_spell(hotkey_ui, hotkey)
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
        logger.debug(f"Move cursor to: ({x}, {y})")
        interception.move_to(x, y)

    def _left_click(self):
        logger.debug("Left click")
        interception.click(button="left")

    def _right_click(self):
        logger.debug("Right click")
        interception.click(button="right")

    def _try_cast_spell(self, hotkey_ui: GameRec, hotkey: str):
        screenshot = self.window.capture(hotkey_ui)
        if is_hotkey_castable(screenshot):
            self._hold_key("ctrl")
            self._press_key("h")
            self._release_key("ctrl")
            time.sleep(0.05)
            logger.debug(f"Ability {hotkey_ui} ready")
            self._press_key(hotkey)
            self._hold_key("ctrl")
            self._press_key("h")
            self._release_key("ctrl")
        else:
            logger.debug(f"Ability {hotkey_ui} not ready")

    def _stuck_detection(self, coordinates_ui: GameRec):
        screenshot = self.window.capture(coordinates_ui)
        coordinates = read_coordinates(screenshot)
        if (coordinates == self.last_coordinates):
            self.stagnant_frames += 1
            if (self.stagnant_frames >= self.stagnant_threshold):
                logger.info("Character is stucked. Trying to unstuck...")
                # unstuck
                self.stagnant_frames = 0
            else:
                logger.debug(f"Coordinates identical to previous frame for {self.stagnant_frames}/{self.stagnant_threshold} frames")
        else:
            logger.debug(f"Coordinates updated")
            self.stagnant_frames = 0

        def unstuck(duration: int, click_interval: float, screen_fraction: float): # TODO: Parametrize
            ...
