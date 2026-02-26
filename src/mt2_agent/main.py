from .game_interface import GameInterface
from .window_manager import Window, Screenshot
from .game_elements import GamePt, GameRec

from . import nothyr as noth

import argparse
import time
from datetime import datetime
import os
import logging

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


class MetinAgent:
    game: GameInterface
    window: Window
    agent_active: bool
    last_run_start: time
    last_update: time

    def __init__(self, game: GameInterface, window: Window):
        self.game = game
        self.window = window
        self.agent_active = False

    def run(self, args: argparse.Namespace):
        UPDATE_INTERVAL = args.update_interval
        DURATION = args.duration
        SCREENSHOT_PATH = args.screenshot_path

        self.agent_active = True
        self.last_run_start = time.time()

        while DURATION is None or time.time() - self.last_run_start < DURATION:
            self.last_update = time.perf_counter()
            
            self.assertWindowAlive()
            self.assertWindowFocused()

            if (self.agent_active):
                self.window.capture()

            elapsed = time.perf_counter() - self.last_update
            time.sleep(max(0, UPDATE_INTERVAL - elapsed))

    def assertWindowAlive(self):
        try:
            self.window.assertAlive()
        except RuntimeError:
                raise RuntimeError(f'Game not running')
        
    def assertWindowFocused(self):
        focused = self.window.isFocused()

        if focused and not self.active:
            self.toggleAgentActive()
        elif not focused and self.active:
            self.toggleAgentActive()

    def toggleAgentActive(self):
        if self.agent_active:
            logger.info("Agent paused")
        else:
            logger.info("Agent resumed")

    def takeScreenshot(gameRec: GameRec) -> Screenshot:
        

    def getScreen(screenshot: Screenshot):
        screenshot.save(os.path.join(args.screenshot_path, f"{timestamp}.png"))

        
    
if __name__ == "__main__":
    main()