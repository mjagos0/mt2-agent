from . import window_manager as wm
from . import nothyr as nthr

import argparse
import time
from datetime import datetime
import os
import logging

PROG = "Metin2 Agent"
USAGE = "..."
DESCRIPTION = "..."

SCREENSHOT_PATH = "screenshots"
TICK_RATE = 1.0

logger = logging.getLogger(__name__)

# Overlay:
# https://i.giphy.com/Z8MYSDbE8VFqo.webp
# https://media.tenor.com/HErW9lJMDaEAAAAM/cat-asleep-monjjunirawr.gif

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
    
    assert_project()
    window = wm.Window(nthr.WINDOW_CLASS_NAME, nthr.WINDOW_NAME)

    agent_loop(window, args)

def agent_loop(window: wm.Window, args: argparse.Namespace):
    tick_rate = args.tick_rate or TICK_RATE
    screenshot_path = args.screenshot_path or SCREENSHOT_PATH

    active = True

    time.sleep(3)
    window.forceFocus()

    while True:
        start = time.perf_counter()

        window.assertAlive()
        focused = window.isFocused()

        if focused and not active:
            logger.info("Agent resumed")
        elif not focused and active:
            logger.info("Agent paused")

        active = focused

        if active:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            window.capture().save(os.path.join(screenshot_path, f"{timestamp}.png"))

        elapsed = time.perf_counter() - start
        time.sleep(max(0, tick_rate - elapsed))

def handle_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog=PROG,
        usage=USAGE,
        description=DESCRIPTION
    )

    p.add_argument("--tick-rate", type=float, help="Redefine relative screenshot path")

    # Gameplay Features

    # Paths
    p.add_argument("--screenshot-path", help="Redefine relative screenshot path")

    # Developer
    p.add_argument("--debug", action='store_true', help="Show developer logs")

    return p.parse_args()
    

def assert_project():
    os.makedirs(SCREENSHOT_PATH, exist_ok=True)


if __name__ == "__main__":
    main()