from .window_manager import Screenshot

import cv2
import numpy as np
from pathlib import Path

def find_icon(
    screenshot: Screenshot,
    templates: list[tuple[str, np.ndarray]],
    threshold: float = 0.85
) -> tuple[str, int, int] | None:
    gray = cv2.cvtColor(screenshot.data, cv2.COLOR_RGB2GRAY)

    for name, tmpl in templates:
        result = cv2.matchTemplate(gray, tmpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val >= threshold:
            return (name, max_loc[0], max_loc[1])

    return None

# TODO: Preload images on startup in game_executor
# https://claude.ai/chat/3dc07117-3831-4b44-b55b-bee5302bce8f