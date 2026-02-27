from .game_interface import GameInterface
from .window_manager import Window
from .game_executor import GameExecutor
from .game_ui import GameUI
from .game_keys import GameKeys
from .game_actions import PressKey

from . import nothyr as noth

import argparse
import time
import os
import logging
import heapq
from dataclasses import dataclass, field

PROG = "Metin2 Agent"
USAGE = "..."
DESCRIPTION = "..."

DEFAULT_SCREENSHOT_PATH = "screenshots"
DEFAULT_UPDATE_INTERVAL = 1000

logger = logging.getLogger(__name__)

# Overlay:
# https://i.giphy.com/Z8MYSDbE8VFqo.webp
# https://media.tenor.com/HErW9lJMDaEAAAAM/cat-asleep-monjjunirawr.gif

SERVERS = {
    "Nothyr": noth.Nothyr
}

def main():
    args = handle_args()
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if args.debug:
        logging.getLogger('mt2_agent').setLevel(logging.DEBUG)
    else:
        logging.getLogger('mt2_agent').setLevel(logging.INFO)
    
    assert_project(args)
    game = get_game(args)
    window = get_window(game)
    window.forceFocus()

    agent = MetinAgent(game, window)
    agent.run(args)

def handle_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog=PROG,
        usage=USAGE,
        description=DESCRIPTION
    )

    p.add_argument("server", type=str, choices=["Nothyr"], help="Name of Metin2 server")
    p.add_argument("--update-interval", type=float, default=DEFAULT_UPDATE_INTERVAL, help="Interval between agent's actions")
    p.add_argument("--duration", type=float, default=None, help="Duration of the run / agents execution in seconds")

    # Gameplay Features

    # Paths
    p.add_argument("--screenshot-path", default=DEFAULT_SCREENSHOT_PATH, help="Redefine relative screenshot path")

    # Advanced
    p.add_argument("--executor-throttle", type=float, default=0.0, help="Adds delay between every action of an executor")

    # Developer
    p.add_argument("--debug", action='store_true', help="Show developer logs")

    return p.parse_args()
    

def assert_project(args: argparse.Namespace) -> None:
    os.makedirs(args.screenshot_path, exist_ok=True)

def get_game(args: argparse.Namespace) -> GameInterface:
    if args.server not in SERVERS:
        raise ValueError(f"Unknown server: '{args.server}'. Choose from: {list(SERVERS.keys())}")
    return SERVERS[args.server]()
    
def get_window(game: GameInterface):
    try:
        window = Window()
        window.findWindow(game.WINDOW_CLASS_NAME)
        return window
    except RuntimeError:
        raise RuntimeError(f'Could not find window {game.SERVER} window. Is the game running?')


@dataclass(order=True)
class ScheduledTask:
    next_run: float
    name: str = field(compare=False)
    action_fn: callable = field(compare=False)
    interval: float = field(compare=False)


class MetinAgent:
    def __init__(self, game: GameInterface, window: Window):
        self.game = game
        self.window = window
        self.executor: GameExecutor | None = None
        self._heap: list[ScheduledTask] = []

    def _schedule(self, name: str, action_fn, interval: float):
        task = ScheduledTask(
            next_run=time.monotonic(),
            name=name,
            action_fn=action_fn,
            interval=interval,
        )
        heapq.heappush(self._heap, task)

    def run(self, args: argparse.Namespace):

        self.window.capture(GameUI.COORDINATES).save("coordinates.png")
        return
        self.executor = GameExecutor(self.window, args.executor_throttle)
        update_interval = args.update_interval / 1000

        # Register all periodic tasks (including the main loop)
        self._schedule("spells", self.game.try_cast_spells, update_interval)
        self._schedule("pickup", self.game.pickup_items, 0.5)
        self._schedule("cape",   self.game.bravery_cape,  3.0)

        while self._should_run(args):
            # Peek at the earliest task — O(1)
            task = self._heap[0]

            sleep_for = task.next_run - time.monotonic()
            if sleep_for > 0:
                time.sleep(sleep_for)

            # Pop and execute
            task = heapq.heappop(self._heap)
            self.executor.execute(task.action_fn())

            # Reschedule
            task.next_run = time.monotonic() + task.interval
            heapq.heappush(self._heap, task)

    def _should_run(self, args: argparse.Namespace) -> bool:
        if args.duration is None:
            return True
        return time.monotonic() - self.last_run_start < args.duration

    def assertWindowAlive(self):
        try:
            self.window.assertAlive()
        except RuntimeError:
                raise RuntimeError(f'Game not running')
        
    def assertWindowFocused(self):
        focused = self.window.isFocused()

        if focused and not self.agent_active:
            self.toggleAgentActive()
        elif not focused and self.agent_active:
            self.toggleAgentActive()

    def toggleAgentActive(self):
        if self.agent_active:
            logger.info("Agent paused")
        else:
            logger.info("Agent resumed")

    # def take_screenshot(self, screenshot_path: str):
    #     screenshot = self.window.capture()
    #     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    #     screenshot.save(os.path.join(screenshot_path, f"{timestamp}.png"))
    
if __name__ == "__main__":
    main()