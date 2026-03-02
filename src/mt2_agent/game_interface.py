from .window import Window, ScreenPt, ScreenRectangle, Screenshot
from .game_input import GameInputs, Input, MovementType
from .game_ui import GameUI, GameRectangle, GamePt
from .asset_manager import AssetManager, Asset, AssetImage, AssetGroup
from .stuck_detection import StuckDetector

from .util_ability_ready import is_hotkey_castable
from .util_text_detection import read_coordinates, read_text
from .util_object_detection import ObjectDetector, Label
from .util_template_matching import find_first, find_template

from abc import ABC, abstractmethod
from typing import Any
import argparse
import time
import logging
from pathlib import Path
from datetime import datetime
import inspect

logger = logging.getLogger(__name__)


class GameInterface(ABC):
    SERVER: str
    WINDOW_CLASS_NAME: str
    WINDOW_NAME: str

    args: argparse.Namespace
    inputs: GameInputs
    ui: GameUI
    window: Window

    stuck: StuckDetector
    obj_det: ObjectDetector
    asset: AssetManager

    def __init__(self, args: argparse.Namespace, input_overrides: dict):
        self._get_window()

        self.args = args
        self.inputs = GameInputs(min_action_delay=args.input_delay, **input_overrides)
        self.ui = GameUI()

        self.stuck = StuckDetector(args.unstuck_check_interval, args.unstuck_threshold)
        self.obj_det = ObjectDetector(
            args.obj_model_path,
            args.obj_model_confidence_cutoff,
            args.target_boss,
            args.target_boulder,
            args.target_enemy,
        )
        self.asset = AssetManager(args.asset_icon_dir)

    def __init_subclass__(cls, **kwargs: Any):
        super().__init_subclass__(**kwargs)
        required = ("SERVER", "WINDOW_CLASS_NAME", "WINDOW_NAME")
        missing = [attr for attr in required if not hasattr(cls, attr)]
        if missing:
            raise TypeError(f"{cls.__name__} must define: {', '.join(missing)}")

    def _get_window(self):
        try:
            self.window = Window()
            self.window.findWindow(self.WINDOW_CLASS_NAME)
            self.window.forceFocus()

        except RuntimeError:
            raise RuntimeError(
                f"Could not find window {self.SERVER} window. Is the game running?"
            )

    def _debug_capture(self, gameRec: GameRectangle, filename: str = "") -> Screenshot:
        screenshot = self.window.capture(gameRec)
        if self.args.debug:
            caller = inspect.stack()[1].function
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            folder = Path(self.args.debug_folder_screenshots, caller)
            folder.mkdir(parents=True, exist_ok=True)
            screenshot.save(folder / f"{ts}_{filename}.png")
        return screenshot

    def cast_spell(self, gameRec: GameRectangle, hotkey: Input):
        screenshot = self._debug_capture(gameRec, f"spell_{hotkey.keyboard.key}")
        if is_hotkey_castable(screenshot):
            logger.info(f'Casting spell "{hotkey.keyboard.key}"')
            self.inputs.execute(self.inputs.TOGGLE_HORSE)
            self.inputs.execute(hotkey)
            self.inputs.execute(self.inputs.TOGGLE_HORSE)
        else:
            logger.debug(f'Spell "{hotkey.keyboard.key}" unavailable')

    def cast_spells(self):
        if not self.stuck.is_stationary:
            logger.debug("Character is moving, skip spell casting")
            return

        self.cast_spell(self.ui.HOTKEY_1, self.inputs.HOTKEY_1)
        self.cast_spell(self.ui.HOTKEY_2, self.inputs.HOTKEY_2)
        self.cast_spell(self.ui.HOTKEY_3, self.inputs.HOTKEY_3)
        self.cast_spell(self.ui.HOTKEY_4, self.inputs.HOTKEY_4)

        self.cast_spell(self.ui.HOTKEY_F1, self.inputs.HOTKEY_F1)
        self.cast_spell(self.ui.HOTKEY_F2, self.inputs.HOTKEY_F2)
        self.cast_spell(self.ui.HOTKEY_F3, self.inputs.HOTKEY_F3)
        self.cast_spell(self.ui.HOTKEY_F4, self.inputs.HOTKEY_F4)

    def bravery_cape(self):
        self.inputs.execute(self.inputs.BRAVERY_CAPE)

    def pickup_items(self):
        self.inputs.execute(self.inputs.PICKUP_ITEMS)

    def unstuck(self):
        self.inputs.execute(self.inputs.DROP_METIN_QUEUE)
        for _ in range(self.args.unstuck_clicks):
            pt = self.window.random_point_from_center(self.args.unstuck_center_radius)
            self.inputs.click(pt)
            time.sleep(self.args.unstuck_interval)

    def stuck_detection(self):
        screenshot = self._debug_capture(self.ui.COORDINATES, "coordinates")
        coordinates = read_coordinates(screenshot)
        if coordinates is None:
            logger.info(
                "Coordinates are occluded, or otherwise not visible on the screen. Stuck detection will not work."
            )
            return

        if self.stuck.is_stuck(coordinates):
            self.unstuck()

    def auto_target(self):
        screenshot = self.window.capture()
        result = self.obj_det.detect(screenshot)

        if self.args.debug:
            result.annotated().save(
                Path(
                    self.args.debug_folder_screenshots,
                    f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_detections.png",
                )
            )  # TODO: Should unify with _debug_capture or sth

        obj = self.obj_det.detect_priority(result)

        if not obj:
            logger.debug("No target detected.")
            if self.args.target_random:
                pt = self.window.random_point_from_center(
                    self.args.unstuck_center_radius
                )
                self.inputs.click(pt)
            return

        center = obj.center
        logger.debug(f"Auto-targetting {obj.label}.")
        if obj.label == Label.BOSS:
            self.inputs.execute(self.inputs.DROP_METIN_QUEUE)
            self.inputs.click(center)
        elif obj.label == Label.BOULDER:
            self.inputs.click(center, "right", modifier=self.inputs.SHIFT)
        elif obj.label == Label.ENEMY:
            self.inputs.click(center)
        else:
            raise RuntimeError(f'Unknown object type "{obj.label}"')

    def captcha(self):
        trigger_window = self._debug_capture(self.ui.CAPTCHA_DETECT, "captcha-trigger")
        if not find_template(
            trigger_window, self.asset.get_group("nothyr").assets[0]
        ):  # TODO - remove constant, also assets[0] is bad
            logger.debug("Captcha window not detected")
            return

        logger.info("Captcha window detected")
        prompt = self._debug_capture(self.ui.CAPTCHA_PROMPT, "captcha-prompt")
        text = read_text(prompt)
        logger.info(f"Looking for {text}")
        item = text.split(" ")[1]

        challenge = self._debug_capture(self.ui.CAPTCHA_CHALLENGE, "captcha-challenge")
        result = find_first(challenge, self.asset.get_group(item))
        if not result:
            logger.info("Failed to solve Captcha")
            return

        logger.info(f"Solution found")
        x, y = result[1]
        itemPt = ScreenPt(
            challenge.origin_x + x, challenge.origin_y + y
        )  # TODO: Not good
        targetRect = self.window.gamerec_to_screenrec(self.ui.CAPTCHA_TARGET)

        self.inputs.click(itemPt, movement=MovementType.Bezier)
        self.inputs.click(targetRect.center, movement=MovementType.Bezier)

    def biolog(self):
        self.inputs.execute(self.inputs.OPEN_BIOLOG_KEY)

        self.inputs.click(self.window.gamept_to_screenpt(self.ui.BIOLOG_SHOP))
        self.inputs.click(
            self.window.gamept_to_screenpt(self.ui.BIOLOG_ORC_TOOTH), "right"
        )
        self.inputs.click(self.window.gamept_to_screenpt(self.ui.BIOLOG_CONFIRM))
