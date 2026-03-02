from dataclasses import dataclass
import numpy as np
import cv2
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Screenshot:
    data: np.ndarray
    origin_x: int
    origin_y: int

    @property
    def height(self) -> int:
        return self.data.shape[0]

    @property
    def width(self) -> int:
        return self.data.shape[1]

    def screenPt(self, x: int, y: int) -> tuple[int, int]:
        return (self.origin_x + x, self.origin_y + y)

    def screenPtCenter(self) -> tuple[int, int]:
        """Return the screen coordinate of this screenshot's center."""
        return (self.origin_x + self.width // 2, self.origin_y + self.height // 2)

    def save(self, path: Path) -> None:
        if cv2.imwrite(path, cv2.cvtColor(self.data, cv2.COLOR_RGB2BGR)):
            logger.debug(f"Screenshot saved to {path}")
        else:
            raise RuntimeError(f"Failed to save screenshot to {path}")
