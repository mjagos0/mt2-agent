from dataclasses import dataclass
import numpy as np
import cv2
import logging

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class Screenshot:
    data: np.ndarray
    x_offset: int
    y_offset: int

    @property
    def height(self) -> int:
        return self.data.shape[0]

    @property
    def width(self) -> int:
        return self.data.shape[1]
    
    def save(self, path: str) -> None:
        if cv2.imwrite(path, cv2.cvtColor(self.data, cv2.COLOR_RGB2BGR)):
            logger.debug(f"Screenshot saved to {path}")
        else:
            raise RuntimeError(f"Failed to save screenshot to {path}")
