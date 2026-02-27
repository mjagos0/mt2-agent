from .window_manager.screenshot import Screenshot

import numpy as np
import logging

logger = logging.getLogger(__name__)

DARK_THRESHOLD = 15
CONSUMABLE_DARK_FRACTION = 0.15
BUFF_OUTER_BRIGHTNESS = 90
COOLDOWN_QUAD_RANGE = 12


def is_hotkey_castable(screenshot: Screenshot) -> bool:
    """
    Determine whether a hotbar icon represents a castable ability.

    Returns False if the icon is:
      - A consumable item (black background, not a spell)
      - A buff that is currently active (bright blue aura on outer frame)
      - A spell on cooldown (clockwise shadow creates quadrant brightness imbalance)

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
        logger.debug("Ability unavailable: buff active (outer_brightness=%.1f)", outer_brightness)
        return False

    # --- Check 3: Cooldown shadow (quadrant brightness imbalance) ---
    border = 5
    inner = brightness[border:h - border, border:w - border]
    ih, iw = inner.shape
    cy, cx = ih // 2, iw // 2

    quad_means = [
        inner[:cy, :cx].mean(),
        inner[:cy, cx:].mean(),
        inner[cy:, :cx].mean(),
        inner[cy:, cx:].mean(),
    ]
    quad_range = max(quad_means) - min(quad_means)
    if quad_range > COOLDOWN_QUAD_RANGE:
        logger.debug("Ability unavailable: on cooldown (quad_range=%.1f)", quad_range)
        return False

    return True