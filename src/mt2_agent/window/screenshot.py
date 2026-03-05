from dataclasses import dataclass
import numpy as np
import cv2
import logging
from pathlib import Path
from datetime import datetime

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
        if cv2.imwrite(str(path), cv2.cvtColor(self.data, cv2.COLOR_RGB2BGR)):
            logger.debug(f"Screenshot saved to {path}")
        else:
            raise RuntimeError(f"Failed to save screenshot to {path}")

    def annotated(self, event: str, timestamp: datetime | None = None) -> "Screenshot":
        """Return a copy with an event label and timestamp burned into the image.

        The annotation is rendered as white text on a semi-transparent dark
        banner at the top of the image so it is always readable regardless
        of background content.
        """
        ts = timestamp or datetime.now()
        text = f"[{ts.strftime('%Y-%m-%d %H:%M:%S')}] {event}"

        img = self.data.copy()
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 1
        color = (255, 255, 255)

        (tw, th), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        banner_h = th + baseline + 16
        # Semi-transparent dark banner
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (img.shape[1], banner_h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, img, 0.4, 0, img)
        # Text
        cv2.putText(img, text, (8, th + 8), font, font_scale, color, thickness, cv2.LINE_AA)

        return Screenshot(data=img, origin_x=self.origin_x, origin_y=self.origin_y)