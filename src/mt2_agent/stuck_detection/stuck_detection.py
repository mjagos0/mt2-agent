import math
import logging

logger = logging.getLogger(__name__)

DEFAULT_MOVE_TOLERANCE = 3


class StuckDetector:
    check_interval: int
    stagnant_duration_threshold: int
    move_tolerance: float

    stagnant_frames: int
    last_coordinates: tuple[int, int]

    def __init__(self, check_interval: int, stagnant_duration_threshold: int, move_tolerance: float = DEFAULT_MOVE_TOLERANCE):
        self.check_interval = check_interval
        self.stagnant_duration_threshold = stagnant_duration_threshold
        self.move_tolerance = move_tolerance

        self.stagnant_frames = 0
        self.last_coordinates = (0, 0)

    @staticmethod
    def _distance(a: tuple[int, int], b: tuple[int, int]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def is_stuck(self, current_coordinates: tuple[int, int]) -> bool:
        dist = self._distance(current_coordinates, self.last_coordinates)
        logger.debug(f"Coordinates: {current_coordinates} (moved {dist:.1f})")
        if dist <= self.move_tolerance:
            self.stagnant_frames += 1
            logger.debug(
                f"Character did not move for {self.stuck_duration}/{self.stagnant_duration_threshold} seconds"
            )
        else:
            self.stagnant_frames = 0

        self.last_coordinates = current_coordinates

        if self.stuck_duration >= self.stagnant_duration_threshold:
            self.stagnant_frames = 0
            return True
        else:
            return False

    @property
    def stuck_duration(self) -> int:
        return self.check_interval * self.stagnant_frames

    @property
    def is_stationary(self) -> bool:
        return self.stagnant_frames > 0