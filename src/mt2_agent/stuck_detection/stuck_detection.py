import logging

logger = logging.getLogger(__name__)


class StuckDetector:
    check_interval: int
    stagnant_duration_threshold: int

    stagnant_frames: int
    last_coordinates: tuple[int, int]

    def __init__(self, check_interval: int, stagnant_duration_threshold: int):
        self.check_interval = check_interval
        self.stagnant_duration_threshold = stagnant_duration_threshold

        self.stagnant_frames = 0
        self.last_coordinates = (0, 0)

    def is_stuck(self, current_coordinates: tuple[int, int]) -> bool:
        logger.debug(f"Coordinates: {current_coordinates}")
        if current_coordinates == self.last_coordinates:
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
