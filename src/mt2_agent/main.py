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
    p = argparse.ArgumentParser(prog=PROG, usage=USAGE, description=DESCRIPTION)

    p.add_argument("server", type=str, choices=["Nothyr"], help="Name of Metin2 server")

    # Input overrides
    p.add_argument(
        "--rebind",
        nargs=2,
        action="append",
        metavar=("NAME", "KEY"),
        help="Rebind a hotkey, e.g. --rebind HOTKEY_1 q --rebind PICKUP_ITEMS x",
    )
    p.add_argument(
        "--input-delay",
        type=float,
        default = 0.06,
        help="Average delay between agent inputs (i.e. delay between moving a mouse and pressing a left click)"
    )

    p.add_argument(
        "--duration",
        type=int,
        default=None,
        help="Duration of the run / agents execution in seconds",
    )

    # Features frequency
    p.add_argument(
        "--auto-cast-interval",
        type=int,
        default=1,
        help="How often to cast spells off cooldown. 0 to disable",
    )
    p.add_argument(
        "--auto-pickup-interval",
        type=int,
        default=1,
        help="How often to pick up items from ground. 0 to disable",
    )
    p.add_argument(
        "--auto-cape-interval",
        type=int,
        default=3,
        help="How often to use the cape. 0 to disable",
    )
    p.add_argument(
        "--unstuck-check-interval",
        type=int,
        default=5,
        help="How often to check character coordinates",
    )
    p.add_argument(
        "--auto-target-interval",
        type=int,
        default=3,
        help="How often to detect targets",
    )
    p.add_argument(
        "--captcha-check",
        type=int,
        default=3,
        help="How often to check for captcha window",
    )

    # Stuck detection
    p.add_argument(
        "--unstuck-threshold",
        type=int,
        default=60,
        help="Number of seconds to remain in the same place to execute unstuck procedure",
    )
    p.add_argument(
        "--unstuck-clicks",
        type=int,
        default=30,
        help="Number of clicks during unstuck procedure",
    )
    p.add_argument(
        "--unstuck-interval",
        type=float,
        default=0.1,
        help="Duration between clicks during unstuck procedure",
    )
    p.add_argument(
        "--unstuck-center-radius",
        type=float,
        default=0.65,
        help="Percentual radius from center of the screen for clicks during unstuck procedure",
    )

    # Auto target
    p.add_argument(
        "--target-boss",
        type=int,
        default=0,
        help="Auto target boss priority. 0 for off.",
    )
    p.add_argument(
        "--target-boulder",
        type=int,
        default=3,
        help="Auto target boulder priority. 0 for off.",
    )
    p.add_argument(
        "--target-enemy",
        type=int,
        default=0,
        help="Auto target enemy priority. 0 for off.",
    )
    p.add_argument(
        "--target-random",
        type=int,
        default=0,
        help="Auto target random spot priority. 0 for off.",
    )

    # Captcha
    p.add_argument(
        "--captcha-trigger-template-path",
        type=str,
        default="assets/nothyr/captcha-detect.png",
        help="Path to Captcha trigger image template",
    )

    # Detection model
    p.add_argument(
        "--obj-model-path",
        type=str,
        default="assets/model/best.pt",
        help="Path to YOLOv11 model weights",
    )
    p.add_argument(
        "--obj-model-confidence-cutoff",
        type=float,
        default=0.3,
        help="Detection confidence threshold",
    )

    # Assets
    p.add_argument(
        "--asset-icon-dir",
        type=str,
        default="assets/icons",
        help="Path to folder with game icons",
    )

    # Screenshots
    p.add_argument(
        "--screenshot-path",
        default=DEFAULT_SCREENSHOT_PATH,
        help="Redefine relative screenshot path",
    )

    # Developer
    p.add_argument("--debug", action="store_true", help="Show developer logs")
    p.add_argument(
        "--debug-folder", default="debug", help="Developer folder for debugging"
    )
    p.add_argument(
        "--debug-folder-screenshots",
        default="debug",
        help="Developer folder for debug screenshots",
    )

    args = p.parse_args()

    assert (
        args.unstuck_threshold > args.unstuck_check_interval
    ), f"--unstuck-threshold ({args.unstuck_threshold}) must be larger than --stuck-check-interval ({args.unstuck_check_interval})"

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

    def _schedule(self, name: str, action_fn: Callable[[], None], interval: float):
        if interval == 0:
            logger.info(f"{name} not scheduled")
            return
        else:
            logger.info(f"{name} scheduled to run every {interval}s")
            task = ScheduledTask(
                next_run=time.monotonic(),
                name=name,
                action_fn=action_fn,
                interval=interval,
            )
            heapq.heappush(self._heap, task)

    def run(self):
        # self.game.window.capture(self.game.ui.HOTKEY_F1).save(Path("HOTKEY_F1.png"))
        # self.game.window.capture(self.game.ui.HOTKEY_F2).save(Path("HOTKEY_F2.png"))
        # self.game.window.capture(self.game.ui.HOTKEY_F3).save(Path("HOTKEY_F3.png"))
        # self.game.window.capture(self.game.ui.HOTKEY_F4).save(Path("HOTKEY_F4.png"))
        # logger.info(self.game.window.getScaleFactor())

        # return

        # self.game.window.capture(self.game.ui.CAPTCHA_DETECT).save(Path("Captcha.png"))
        # return
        # self.game.pickup_items()
        # return
        # Register all periodic tasks
        self._schedule("login", self.game.login, 5)
        self._schedule("respawn", self.game.respawn, 5)
        self._schedule("auto-cast", self.game.cast_spells, self.args.auto_cast_interval)
        self._schedule(
            "auto-pickup", self.game.pickup_items, self.args.auto_pickup_interval
        )
        # self._schedule("auto-cape", self.game.bravery_cape, self.args.auto_cape_interval)
        self._schedule(
            "stuck-detection",
            self.game.stuck_detection,
            self.args.unstuck_check_interval,
        )
        self._schedule(
            "auto-target", self.game.auto_target, self.args.auto_target_interval
        )
        self._schedule("captcha", self.game.captcha, self.args.captcha_check)
        # self._schedule("biolog", self.game.biolog, 5)
        

        while self._should_run():
            self.assertWindowAlive()
            self.assertWindowFocused()

            if not self._agent_active:
                time.sleep(0.1)
                continue

            # Peek at the earliest task — O(1)
            task = self._heap[0]

            sleep_for = task.next_run - time.monotonic()
            if sleep_for > 0:
                time.sleep(sleep_for)

            # Pop and execute
            task = heapq.heappop(self._heap)
            task.action_fn()

            # Reschedule
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
