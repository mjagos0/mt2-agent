from .window import Window, ScreenPt, Screenshot
from .game_input import GameInputs, Input, MovementType
from .game_ui import GameUI, GameRectangle
from .asset_manager import AssetManager, AssetImage
from .stuck_detection import StuckDetector

from .util_ability_ready import is_hotkey_castable
from .util_text_detection import read_coordinates, read_text
from .util_object_detection import ObjectDetector, Label
from .util_template_matching import find_first, find_template

from abc import ABC
from typing import Any
import argparse
import time
import logging
import cv2
from pathlib import Path
from datetime import datetime
import inspect
import difflib

logger = logging.getLogger(__name__)


class GameInterface(ABC):
    SERVER: str
    WINDOW_CLASS_NAME: str
    WINDOW_NAME: str
    SERVER_ASSETS: str

    args: argparse.Namespace
    inputs: GameInputs
    ui: GameUI
    window: Window

    stuck: StuckDetector
    obj_det: ObjectDetector
    asset: AssetManager

    def __init__(self, args: argparse.Namespace, input_overrides: dict[str, Input]):
        self._get_window()

        self.args = args
        self.inputs = GameInputs(**input_overrides)
        self.ui = GameUI()

        self.stuck = StuckDetector(args.unstuck_threshold)
        self.obj_det = ObjectDetector(
            args.obj_model_path,
            args.obj_model_confidence_cutoff,
        )
        self.asset = AssetManager(args.asset_icon_dir)

    def __init_subclass__(cls, **kwargs: Any):
        super().__init_subclass__(**kwargs)
        required = ("SERVER", "WINDOW_CLASS_NAME", "WINDOW_NAME", "SERVER_ASSETS")
        missing = [attr for attr in required if not hasattr(cls, attr)]
        if missing:
            raise TypeError(f"{cls.__name__} must define: {', '.join(missing)}")

    def _get_window(self):
        try:
            self.window = Window()
            self.window.findWindow(self.WINDOW_CLASS_NAME)
            self.window.forceFocus()
            time.sleep(1)

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

    # ------------------------------------------------------------------
    # Event & periodic screenshots
    # ------------------------------------------------------------------

    def event_screenshot(self, event: str) -> None:
        """Capture a full-window screenshot annotated with *event* and save it.

        Only fires when the ``screenshots_events`` flag is True in args.
        """
        if not getattr(self.args, "screenshots_events", False):
            return

        try:
            screenshot = self.window.capture()
            annotated = screenshot.annotated(event)
            folder = Path(self.args.screenshot_path)
            folder.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            safe_event = event.replace(" ", "_").replace(":", "-")
            filename = f"{ts}_{safe_event}.png"
            annotated.save(folder / filename)
            logger.info("Screenshot saved: %s -> %s", event, filename)
        except Exception:
            logger.exception("Failed to save event screenshot for '%s'", event)

    def periodic_screenshot(self) -> None:
        """Take a periodic screenshot (called by the scheduler)."""
        try:
            screenshot = self.window.capture()
            annotated = screenshot.annotated("periodic")
            folder = Path(self.args.screenshot_path)
            folder.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{ts}_periodic.png"
            annotated.save(folder / filename)
            logger.info("Screenshot saved: %s", filename)
        except Exception:
            logger.exception("Failed to save periodic screenshot")

    # ------------------------------------------------------------------
    # Game actions
    # ------------------------------------------------------------------

    def cast_spell(self, gameRec: GameRectangle, hotkey: Input):
        if hotkey.keyboard is None or hotkey.keyboard.key is None:
            logger.error("None keyboard or key passed")
            return

        screenshot = self._debug_capture(gameRec, f"spell_{hotkey.keyboard.key}")
        if is_hotkey_castable(screenshot):
            logger.info(f'Casting spell "{hotkey.keyboard.key}"')
            self.inputs.execute(self.inputs.TOGGLE_HORSE, 0.2)
            self.inputs.execute(hotkey, 0.2)
            self.inputs.execute(self.inputs.TOGGLE_HORSE, 0.2)
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
        logger.info(f"Cape ({self.inputs.BRAVERY_CAPE})")

    def pickup_items(self):
        self.inputs.execute(self.inputs.PICKUP_ITEMS)
        logger.info(f"Pick-up items ({self.inputs.PICKUP_ITEMS})")

    def unstuck(self, unstuck_clicks: int, unstuck_interval: float, unstuck_center_radius: float):
        self.inputs.execute(self.inputs.DROP_METIN_QUEUE)
        self.event_screenshot("stuck-detection: unstuck procedure started")
        for _ in range(unstuck_clicks):
            pt = self.window.random_point_from_center(unstuck_center_radius)
            self.inputs.click(pt)
            time.sleep(unstuck_interval)

    def stuck_detection(
        self,
        unstuck_threshold: int,
        unstuck_clicks: int,
        unstuck_interval: float,
        unstuck_center_radius: float
    ):
        screenshot = self._debug_capture(self.ui.COORDINATES, "coordinates")
        coordinates = read_coordinates(screenshot)
        if coordinates is None:
            logger.info(
                "Coordinates are occluded, or otherwise not visible on the screen. Stuck detection will not work."
            )
            return

        # Keep the StuckDetector's threshold in sync with the live param.
        self.stuck.stagnant_duration_threshold = unstuck_threshold

        if self.stuck.is_stuck(coordinates):
            self.unstuck(unstuck_clicks, unstuck_interval, unstuck_center_radius)

    def auto_target(
        self,
        target_boss: int,
        target_boulder: int,
        target_enemy: int,
        target_random: int,
    ):
        screenshot = self.window.capture()
        result = self.obj_det.detect(screenshot)

        if self.args.debug:
            result.annotated().save(
                Path(
                    self.args.debug_folder_screenshots,
                    f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_detections.png",
                )
            )  # TODO: Should unify with _debug_capture or sth

        # Build priority order from the live params.
        obj = self.obj_det.detect_priority(
            result,
            boss_priority=target_boss,
            boulder_priority=target_boulder,
            enemy_priority=target_enemy,
        )

        if not obj:
            logger.debug("No target detected.")
            if target_random > 0:
                pt = self.window.random_point_from_center(
                    self.args.unstuck_center_radius
                )
                self.inputs.click(pt)
            return

        center = obj.center
        logger.debug(f"Auto-targetting {obj.label}.")
        if target_boss and obj.label == Label.BOSS:
            logger.info(f"Found boss at {center}")
            self.inputs.execute(self.inputs.DROP_METIN_QUEUE)
            self.inputs.click(center)
        elif target_boulder and obj.label == Label.BOULDER:
            logger.info(f"Found boulder at {center}")
            self.inputs.click(center, "right", modifier=self.inputs.SHIFT)
        elif target_enemy and obj.label == Label.ENEMY:
            logger.info(f"Found enemy at {center}")
            self.inputs.click(center)
        else:
            raise RuntimeError(f'Unknown object type "{obj.label}"')
        
    def _fuzzy_match_group(self, item: str) -> str:
        """Match OCR text to closest asset group name."""
        groups = list(self.asset.groups.keys())
        matches = difflib.get_close_matches(item, groups, n=1, cutoff=0.5)
        if matches:
            if matches[0] != item:
                logger.info(f"Fuzzy matched '{item}' -> '{matches[0]}'")
            return matches[0]
        logger.warning(f"No close match for '{item}' in {groups}")
        return item

    def captcha(self):
        trigger_window = self._debug_capture(self.ui.CAPTCHA_DETECT, "captcha-trigger")
        template = self.asset.get_group(self.SERVER_ASSETS).assets[0]
        if not isinstance(template, AssetImage):
            logger.warning("Expected AssetImage, got %s", type(template))
            return
    
        if not find_template(trigger_window, template, self.window.getScaleFactor()):
            logger.debug("Captcha window not detected")
            return

        logger.info("Captcha: window detected")
        self.event_screenshot("captcha: window detected")

        prompt = self._debug_capture(self.ui.CAPTCHA_PROMPT, "captcha-prompt")
        text = read_text(prompt)
        if (text is None):
            logger.error("Failed to read text from Captcha prompt")
            self.event_screenshot("captcha: failed to read prompt text")
            return
        else:
            logger.info(f"Captcha: Looking for {text}")

        item = self._fuzzy_match_group(text.split(" ")[1])
        challenge = self._debug_capture(self.ui.CAPTCHA_CHALLENGE, "captcha-challenge")
        result = find_first(challenge, self.asset.get_group(item), self.window.getScaleFactor())
        if not result:
            logger.error("Failed to solve Captcha")
            self.event_screenshot("captcha: failed to solve")
            return
        else:
            logger.info(f"Captcha: Solution found")

        x, y = result[1]
        itemPt = ScreenPt(
            challenge.origin_x + x, challenge.origin_y + y
        )  # TODO: Not good
        targetRect = self.window.gamerec_to_screenrec(self.ui.CAPTCHA_TARGET)

        logger.info(f"Captcha: Moving {itemPt} to {targetRect.center}")
        self.inputs.click(itemPt, movement=MovementType.Bezier, min_delay=0.2)
        self.inputs.click(targetRect.center, movement=MovementType.Bezier, min_delay=1.0)

        self.event_screenshot("captcha: solved")

        if self.args.debug:
            matched_asset = result[0]
            scale = self.window.getScaleFactor()
            th, tw = matched_asset.image.shape[:2]
            tw, th = int(tw * scale), int(th * scale)
            debug_img = challenge.data.copy()
            top_left = (x - tw // 2, y - th // 2)
            bottom_right = (x + tw // 2, y + th // 2)
            cv2.rectangle(debug_img, top_left, bottom_right, (0, 255, 0), 2)
            cv2.circle(debug_img, (x, y), 4, (0, 0, 255), -1)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            folder = Path(self.args.debug_folder_screenshots, "captcha")
            folder.mkdir(parents=True, exist_ok=True)
            debug_screenshot = Screenshot(data=debug_img, origin_x=challenge.origin_x, origin_y=challenge.origin_y)
            debug_screenshot.save(folder / f"{ts}_captcha-solution_{item}.png")

    def login(self):
        trigger_window = self._debug_capture(self.ui.LOGIN_DETECT, "login-trigger")
        template = self.asset.get_group(self.SERVER_ASSETS).assets[1]

        if not isinstance(template, AssetImage):
            logger.warning("Expected AssetImage, got %s", type(template))
            return
    
        if not find_template(trigger_window, template, self.window.getScaleFactor()):
            logger.debug("Login window not detected")
            return
        else:
            logger.info("Login window detected")
        
        self.event_screenshot("login: window detected, attempting login")

        logger.info("Trying to login-in")
        ch3_button = self.window.gamept_to_screenpt(self.ui.LOGIN_CH3)
        self.inputs.click(ch3_button)
        self.inputs.execute(self.inputs.LOGIN_1)
        logger.info("Logged-in")
        time.sleep(5)
        self.inputs.execute(self.inputs.LOGIN_CONFIRM)
        logger.info("Character selected")
        time.sleep(5)

        self.event_screenshot("login: completed")

    def respawn(self):
        trigger_window = self._debug_capture(self.ui.RESPAWN_DETECT, "respawn-trigger")
        template = self.asset.get_group(self.SERVER_ASSETS).assets[2]

        if not isinstance(template, AssetImage):
            logger.warning("Expected AssetImage, got %s", type(template))
            return

        result = find_template(trigger_window, template, self.window.getScaleFactor())
        if not result:
            logger.debug("Respawn window not detected")
            return

        self.event_screenshot("respawn: death detected, attempting respawn")

        logger.info("Trying to respawn")
        x, y = result
        windowCenter = ScreenPt(
            trigger_window.origin_x + x + 1, trigger_window.origin_y + y + 1
        )

        self.inputs.click(windowCenter, movement=MovementType.Bezier)
        logger.info("Respawned")
        self.inputs.execute(self.inputs.TOGGLE_HORSE)
        logger.info("Mounting horse")

        self.event_screenshot("respawn: completed")
        

    def attack(self):
        logger.info("Attack button toggled")
        self.inputs.toggle_key(self.inputs.ATTACK_BUTTON)
        
    def biolog(self):
        confirmPt = self.window.gamept_to_screenpt(self.ui.BIOLOG_CONFIRM)
        self.inputs.execute(self.inputs.OPEN_BIOLOG_KEY, min_delay=1)
        self.inputs.click(confirmPt, movement=MovementType.Bezier, min_delay=1)
        self.inputs.execute(self.inputs.OPEN_BIOLOG_KEY, min_delay=1)