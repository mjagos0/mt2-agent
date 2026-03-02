from .window.screenshot import Screenshot

import numpy as np
import logging

logger = logging.getLogger(__name__)

DARK_THRESHOLD = 15
CONSUMABLE_DARK_FRACTION = 0.15
BUFF_OUTER_BRIGHTNESS = 90
COOLDOWN_RATIO_THRESHOLD = 0.8


def is_hotkey_castable(screenshot: Screenshot) -> bool:
    """
    Determine whether a hotbar icon represents a castable ability.

    Returns False if the icon is:
      - A consumable item (black background, not a spell)
      - A buff that is currently active (bright blue aura on outer frame)
      - A spell on cooldown (shadow at 11 o'clock probe point)

    The cooldown shadow sweeps clockwise from 12 o'clock. The 11 o'clock
    position (slightly left of top-center) is the last spot the shadow
    occupies before the spell becomes ready. We compare brightness there
    against the 1 o'clock position (first to clear) as a reference.
    Shadow halves brightness, giving a ratio of ~0.5 vs ~1.0 when ready.

    Args:
        screenshot: Captured region of the hotbar icon.

    Returns:
        True if the icon is a spell that can be cast, False otherwise.
    """
    arr = screenshot.data.astype(float)
    h, w = arr.shape[:2]
    brightness = (arr[:, :, 0] + arr[:, :, 1] + arr[:, :, 2]) / 3

    # --- Check 1: Consumable (high fraction of near-black pixels) ---
    dark_fraction = (brightness < DARK_THRESHOLD).sum() / brightness.size
    if dark_fraction > CONSUMABLE_DARK_FRACTION:
        logger.debug("Not a spell: consumable (dark_fraction=%.3f)", dark_fraction)
        return False

    # --- Check 2: Buff aura (outer 1px ring glows bright blue-white) ---
    outer = np.zeros((h, w), dtype=bool)
    outer[0, :] = True
    outer[-1, :] = True
    outer[:, 0] = True
    outer[:, -1] = True

    outer_brightness = brightness[outer].mean()
    if outer_brightness > BUFF_OUTER_BRIGHTNESS:
        logger.debug(
            "Ability unavailable: buff active (outer_brightness=%.1f)", outer_brightness
        )
        return False

    # --- Check 3: Cooldown shadow (11 o'clock vs 1 o'clock brightness) ---
    cx = w // 2
    probe_rows = slice(3, 7)
    probe_11 = brightness[probe_rows, cx - 5 : cx - 1].mean()
    probe_1 = brightness[probe_rows, cx + 1 : cx + 6].mean()

    ratio = probe_11 / (probe_1 + 1)
    if ratio < COOLDOWN_RATIO_THRESHOLD:
        logger.debug("Ability unavailable: on cooldown (ratio=%.3f)", ratio)
        return False

    return True
