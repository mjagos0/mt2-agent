from .game_interface import GameInterface
from .window import Window
from .game_input import Input, KeyboardInput

from . import nothyr as noth

import argparse
import time
import os
import logging
import heapq
import shutil
from dataclasses import dataclass, field
from collections.abc import Callable
from pathlib import Path

PROG = "Metin2 Agent"
USAGE = "..."
DESCRIPTION = "..."

DEFAULT_SCREENSHOT_PATH = "screenshots"
DEFAULT_UPDATE_INTERVAL = 1000

logger = logging.getLogger(__name__)

# Overlay:
# https://i.giphy.com/Z8MYSDbE8VFqo.webp
# https://media.tenor.com/HErW9lJMDaEAAAAM/cat-asleep-monjjunirawr.gif

SERVERS = {"Nothyr": noth.Nothyr}


def main():
    args = handle_args()
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if args.debug:
        logging.getLogger("mt2_agent").setLevel(logging.DEBUG)
    else:
        logging.getLogger("mt2_agent").setLevel(logging.INFO)

    input_overrides: dict[str, Input] = {}
    if args.rebind:
        for name, key in args.rebind:
            input_overrides[name] = Input(keyboard=KeyboardInput(key))

    assert_project(args)
    game = get_game(args, input_overrides)
    agent = MetinAgent(args, game)
    agent.run()


def handle_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog=PROG, usage=USAGE, description=DESCRIPTION,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Parameter groups
    server_settings = p.add_argument_group("Core settings")
    features = p.add_argument_group("Features")
    input_settings = p.add_argument_group("Input settings")
    stuck_settings = p.add_argument_group("Stuck detection settings")
    autotarget_settings = p.add_argument_group("Auto-target settings")
    captcha_settings = p.add_argument_group("Captcha settings")
    model_settings = p.add_argument_group("YOLO detection model settings")
    developer_settings = p.add_argument_group("Developer settings")
    assets_settings = p.add_argument_group("Assets settings")

    # Runtime settings
    server_settings.add_argument("server", type=str, choices=["Nothyr"], help="Name of Metin2 server")
    server_settings.add_argument(
        "--duration",
        type=int,
        default=None,
        help="Maximum duration of the agent's runtime in seconds",
    )

    # Features on/off
    features.add_argument("--no-spells", dest="spells", action="store_false", help="Disable spell casting")
    features.add_argument("--no-pickup", dest="pickup", action="store_false", help="Disable item pickup")
    features.add_argument("--no-cape", dest="cape", action="store_false", help="Disable bravery cape")
    features.add_argument("--no-stuck", dest="stuck", action="store_false", help="Disable stuck detection")
    features.add_argument("--no-target", dest="target", action="store_false", help="Disable auto-targeting")
    features.add_argument("--no-captcha", dest="captcha", action="store_false", help="Disable captcha detection")
    features.add_argument("--no-respawn", dest="respawn", action="store_false", help="Disable respawn detection")
    features.add_argument("--no-login", dest="login", action="store_false", help="Disable login detection")
    features.add_argument("--biolog", dest="biolog", action="store_true", help="Enable biolog hand-in")
    features.add_argument("--attack", dest="attack", action="store_true", help="Stand in place and hold spacebar")

    # Feature intervals
    features.add_argument("--spells-interval", type=float, default=2, help="Spell casting interval in seconds")
    features.add_argument("--pickup-interval", type=float, default=0, help="Item pickup interval in seconds")
    features.add_argument("--cape-interval", type=float, default=3, help="Bravery cape interval in seconds")
    features.add_argument("--stuck-interval", type=float, default=5, help="Stuck detection check interval in seconds")
    features.add_argument("--target-interval", type=float, default=3, help="Auto-target interval in seconds")
    features.add_argument("--captcha-interval", type=float, default=5, help="Captcha check interval in seconds")
    features.add_argument("--respawn-interval", type=float, default=5, help="Respawn check interval in seconds")
    features.add_argument("--login-interval", type=float, default=5, help="Login check interval in seconds")
    features.add_argument("--biolog-interval", type=float, default=30, help="Biolog hand-in interval in seconds")
    features.add_argument("--attack-interval", type=float, default=9999999999, help="Attack interval in seconds")

    # Stuck detection
    stuck_settings.add_argument(
        "--unstuck-threshold",
        type=int,
        default=60,
        help="Number of seconds to remain in the same place to execute unstuck procedure",
    )
    stuck_settings.add_argument(
        "--unstuck-clicks",
        type=int,
        default=30,
        help="Number of clicks during unstuck procedure",
    )
    stuck_settings.add_argument(
        "--unstuck-interval",
        type=float,
        default=0.1,
        help="Duration between clicks during unstuck procedure",
    )
    stuck_settings.add_argument(
        "--unstuck-center-radius",
        type=float,
        default=0.65,
        help="Percentual radius from center of the screen for clicks during unstuck procedure",
    )

    # Auto target
    autotarget_settings.add_argument(
        "--target-boss",
        type=int,
        default=0,
        help="Auto target boss priority. 0 for off.",
    )
    autotarget_settings.add_argument(
        "--target-boulder",
        type=int,
        default=3,
        help="Auto target boulder priority. 0 for off.",
    )
    autotarget_settings.add_argument(
        "--target-enemy",
        type=int,
        default=0,
        help="Auto target enemy priority. 0 for off.",
    )
    autotarget_settings.add_argument(
        "--target-random",
        type=int,
        default=0,
        help="Auto target random spot priority. 0 for off.",
    )

    # Captcha
    captcha_settings.add_argument(
        "--captcha-trigger-template-path",
        type=str,
        default="assets/nothyr/captcha-detect.png",
        help="Path to Captcha trigger image template",
    )

    # Input settings
    input_settings.add_argument(
        "--rebind",
        nargs=2,
        action="append",
        metavar=("NAME", "KEY"),
        help="Rebind a hotkey, e.g. --rebind HOTKEY_1 q --rebind PICKUP_ITEMS x",
    )
    input_settings.add_argument(
        "--input-delay",
        type=float,
        default=0.06,
        help="Average delay between agent inputs",
    )

    # Detection model
    model_settings.add_argument(
        "--obj-model-path",
        type=str,
        default="assets/model/best.pt",
        help="Path to YOLOv11 model weights",
    )
    model_settings.add_argument(
        "--obj-model-confidence-cutoff",
        type=float,
        default=0.3,
        help="Detection confidence threshold",
    )

    # Assets
    assets_settings.add_argument(
        "--asset-icon-dir",
        type=str,
        default="assets/icons",
        help="Path to folder with game icons",
    )
    assets_settings.add_argument(
        "--screenshot-path",
        default=DEFAULT_SCREENSHOT_PATH,
        help="Redefine relative screenshot path",
    )

    # Developer
    developer_settings.add_argument("--debug", action="store_true", help="Show developer logs")
    developer_settings.add_argument(
        "--debug-folder", default="debug", help="Developer folder for debugging",
    )
    developer_settings.add_argument(
        "--debug-folder-screenshots",
        default="debug",
        help="Developer folder for debug screenshots",
    )

    args = p.parse_args()

    assert (
        args.unstuck_threshold > args.stuck_interval
    ), f"--unstuck-threshold ({args.unstuck_threshold}) must be larger than --stuck-interval ({args.stuck_interval})"

    return args


def assert_project(args: argparse.Namespace) -> None:
    os.makedirs(args.screenshot_path, exist_ok=True)

    if args.debug:
        if os.path.exists(args.debug_folder):
            shutil.rmtree(args.debug_folder)
        os.makedirs(args.debug_folder, exist_ok=True)
        os.makedirs(args.debug_folder_screenshots, exist_ok=True)


def get_game(args: argparse.Namespace, input_overrides: dict[str, Input]) -> GameInterface:
    if args.server not in SERVERS:
        raise ValueError(
            f"Unknown server: '{args.server}'. Choose from: {list(SERVERS.keys())}"
        )
    return SERVERS[args.server](args, input_overrides)


def get_window(game: GameInterface):
    try:
        window = Window()
        window.findWindow(game.WINDOW_CLASS_NAME)
        return window
    except RuntimeError:
        raise RuntimeError(
            f"Could not find window {game.SERVER} window. Is the game running?"
        )


@dataclass(order=True)
class ScheduledTask:
    next_run: float
    name: str = field(compare=False)
    action_fn: Callable[[], None] = field(compare=False)
    interval: float = field(compare=False)


class MetinAgent:
    def __init__(self, args: argparse.Namespace, game: GameInterface):
        self.args = args
        self.game = game
        self._heap: list[ScheduledTask] = []

        self._agent_active = True
        self._deadline = (
            None if args.duration is None else time.monotonic() + args.duration
        )

    def _schedule(self, name: str, action_fn: Callable[[], None], interval: float, initial_delay: float = 0):
        if interval == 0:
            logger.info(f"{name} not scheduled")
            return
        else:
            logger.info(f"{name} scheduled to run every {interval}s (first run in {initial_delay}s)")
            task = ScheduledTask(
                next_run=time.monotonic() + initial_delay,
                name=name,
                action_fn=action_fn,
                interval=interval,
            )
            heapq.heappush(self._heap, task)

    def _schedule_feature(self, name: str, action_fn: Callable[[], None], enabled: bool, interval: float, initial_delay: float = 0):
        if not enabled:
            logger.info(f"{name} disabled")
            return
        self._schedule(name, action_fn, interval, initial_delay)

    def run(self):
        self._schedule_feature("login", self.game.login, self.args.login, self.args.login_interval)
        self._schedule_feature("respawn", self.game.respawn, self.args.respawn, self.args.respawn_interval)
        self._schedule_feature("auto-cast", self.game.cast_spells, self.args.spells, self.args.spells_interval)
        self._schedule_feature("auto-pickup", self.game.pickup_items, self.args.pickup, self.args.pickup_interval)
        self._schedule_feature("auto-cape", self.game.bravery_cape, self.args.cape, self.args.cape_interval)
        self._schedule_feature("stuck-detection", self.game.stuck_detection, self.args.stuck, self.args.stuck_interval)
        self._schedule_feature("auto-target", self.game.auto_target, self.args.target, self.args.target_interval)
        self._schedule_feature("captcha", self.game.captcha, self.args.captcha, self.args.captcha_interval)
        self._schedule_feature("biolog", self.game.biolog, self.args.biolog, self.args.biolog_interval, 30)
        self._schedule_feature("attack", self.game.attack, self.args.attack, self.args.attack_interval, 2)

        while self._should_run():
            task = self._heap[0]

            sleep_for = task.next_run - time.monotonic()
            if sleep_for > 0:
                time.sleep(sleep_for)

            self.assertWindowAlive()
            self.assertWindowFocused()

            if not self._agent_active:
                time.sleep(0.1)
                continue

            task = heapq.heappop(self._heap)
            task.action_fn()

            task.next_run = time.monotonic() + task.interval
            heapq.heappush(self._heap, task)

    def _should_run(self) -> bool:
        return self._deadline is None or time.monotonic() < self._deadline

    def assertWindowAlive(self):
        try:
            self.game.window.assertAlive()
        except RuntimeError:
            raise RuntimeError(f"Game not running")

    def assertWindowFocused(self):
        focused = self.game.window.isFocused()

        if focused and not self._agent_active:
            self.toggleAgentActive()
        elif not focused and self._agent_active:
            self.toggleAgentActive()

    def toggleAgentActive(self):
        self._agent_active = not self._agent_active
        if self._agent_active:
            logger.info("Agent resumed")
        else:
            logger.info("Agent paused")


if __name__ == "__main__":
    main()