import math
import logging
import time

logger = logging.getLogger(__name__)

DEFAULT_MOVE_TOLERANCE = 3


class StuckDetector:
    def __init__(self, stagnant_duration_threshold: int, move_tolerance: float = DEFAULT_MOVE_TOLERANCE):
        self.stagnant_duration_threshold = stagnant_duration_threshold
        self.move_tolerance = move_tolerance

        self.last_moved_time = time.monotonic()
        self.last_coordinates = (0, 0)

    @staticmethod
    def _distance(a: tuple[int, int], b: tuple[int, int]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def is_stuck(self, current_coordinates: tuple[int, int]) -> bool:
        dist = self._distance(current_coordinates, self.last_coordinates)
        logger.debug(f"Coordinates: {current_coordinates} (moved {dist:.1f})")

        if dist > self.move_tolerance:
            if (self.last_moved_time > 0):
                f"Stuck-detection: Reset"
            self.last_moved_time = time.monotonic()
        else:
            logger.info(
                f"Stuck-detection: {self.stuck_duration:.0f}/{self.stagnant_duration_threshold}s"
            )

        self.last_coordinates = current_coordinates
        return self.stuck_duration >= self.stagnant_duration_threshold

    @property
    def stuck_duration(self) -> float:
        return time.monotonic() - self.last_moved_time

    @property
    def is_stationary(self) -> bool:
        return self.stuck_duration > 0