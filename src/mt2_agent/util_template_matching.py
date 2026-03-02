"""Masked template matching for game item icons."""

from .window import Screenshot
from .asset_manager import AssetImage, AssetGroup

import numpy as np
import cv2
import logging

logger = logging.getLogger(__name__)


def find_template(
    screenshot: Screenshot,
    template: AssetImage,
    match_threshold: float = 0.95,
    bg_threshold: int = 10,
) -> tuple[int, int] | None:
    """Find template in screenshot. Returns (x, y) center or None."""
    source = cv2.cvtColor(screenshot.data, cv2.COLOR_RGB2GRAY)

    mask = np.zeros_like(template.image, dtype=np.uint8)
    mask[template.image >= bg_threshold] = 255

    result = cv2.matchTemplate(source, template.image, cv2.TM_CCORR_NORMED, mask=mask)
    _, score, _, (x, y) = cv2.minMaxLoc(result)

    logger.debug(
        "Template '%s': score=%.4f threshold=%.4f %s",
        template.name,
        score,
        match_threshold,
        "MATCH" if score >= match_threshold else "NO MATCH",
    )

    if score < match_threshold:
        return None

    h, w = template.image.shape
    return (x + w // 2, y + h // 2)


def find_first(
    screenshot: Screenshot,
    group: AssetGroup,
    match_threshold: float = 0.95,
    bg_threshold: int = 10,
) -> tuple[AssetImage, tuple[int, int]] | None:
    """Find the first matching icon from a group. Returns (icon, (x, y)) or None."""
    for asset in group:
        if not isinstance(asset, AssetImage):
            continue
        pos = find_template(screenshot, asset, match_threshold, bg_threshold)
        if pos:
            logger.debug("Group '%s': matched '%s' at %s", group.name, asset.name, pos)
            return (asset, pos)
    logger.debug("Group '%s': no matches found", group.name)
    return None
