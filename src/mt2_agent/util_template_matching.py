"""Masked template matching for game item icons."""

from .window import Screenshot
from .asset_manager import AssetImage, AssetGroup

import numpy as np
import cv2
import logging

logger = logging.getLogger(__name__)

_dump_counter = 0


# def _dump_image(name: str, image: np.ndarray) -> None:
#     """Save a debug image to disk."""
#     global _dump_counter
#     path = f"{_dump_counter:04d}_{name}.png"
#     cv2.imwrite(path, image)
#     logger.debug("Dumped %s -> %s", name, path)
#     _dump_counter += 1


def find_template(
    screenshot: Screenshot,
    template: AssetImage,
    scale: float = 1.0,
    match_threshold: float = 0.95,
    bg_threshold: int = 10,
) -> tuple[int, int] | None:
    """Find template in screenshot. Returns (x, y) center or None."""
    source = cv2.cvtColor(screenshot.data, cv2.COLOR_RGB2GRAY)
    tmpl = template.image
    mask = np.zeros_like(tmpl, dtype=np.uint8)
    mask[tmpl >= bg_threshold] = 255

    # _dump_image(f"{template.name}_template_original", tmpl)
    # _dump_image(f"{template.name}_screenshot", source)

    if scale != 1.0:
        h, w = tmpl.shape
        nw, nh = int(w * scale), int(h * scale)
        tmpl = cv2.resize(tmpl, (nw, nh), interpolation=cv2.INTER_LINEAR)
        mask = cv2.resize(mask, (nw, nh), interpolation=cv2.INTER_NEAREST)
        # _dump_image(f"{template.name}_template_scaled_{scale:.2f}", tmpl)

    result = cv2.matchTemplate(source, tmpl, cv2.TM_CCORR_NORMED, mask=mask)
    _, score, _, (x, y) = cv2.minMaxLoc(result)

    h, w = tmpl.shape

    logger.debug(
        "Template '%s': score=%.4f threshold=%.4f scale=%.2f %s",
        template.name,
        score,
        match_threshold,
        scale,
        "MATCH" if score >= match_threshold else "NO MATCH",
    )

    if score < match_threshold:
        return None

    return (x + w // 2, y + h // 2)


def find_first(
    screenshot: Screenshot,
    group: AssetGroup,
    scale: float = 1.0,
    bg_threshold: int = 0
) -> tuple[AssetImage, tuple[int, int]] | None:
    """Find the best matching icon from a group. Returns (icon, (x, y)) or None."""
    best: tuple[AssetImage, tuple[int, int], float] | None = None

    for asset in group:
        if not isinstance(asset, AssetImage):
            continue

        source = cv2.cvtColor(screenshot.data, cv2.COLOR_RGB2GRAY)
        tmpl = asset.image
        mask = np.zeros_like(tmpl, dtype=np.uint8)
        mask[tmpl >= bg_threshold] = 255

        if scale != 1.0:
            h, w = tmpl.shape
            nw, nh = int(w * scale), int(h * scale)
            tmpl = cv2.resize(tmpl, (nw, nh), interpolation=cv2.INTER_LINEAR)
            mask = cv2.resize(mask, (nw, nh), interpolation=cv2.INTER_NEAREST)

        result = cv2.matchTemplate(source, tmpl, cv2.TM_CCORR_NORMED, mask=mask)
        _, score, _, (x, y) = cv2.minMaxLoc(result)
        h, w = tmpl.shape
        pos = (x + w // 2, y + h // 2)

        logger.debug("Group '%s': asset '%s' score=%.4f at %s", group.name, asset.name, score, pos)

        if best is None or score > best[2]:
            best = (asset, pos, score)

    if best is None:
        logger.debug("Group '%s': no assets to match", group.name)
        return None

    logger.debug("Group '%s': best match '%s' score=%.4f at %s", group.name, best[0].name, best[2], best[1])
    return (best[0], best[1])