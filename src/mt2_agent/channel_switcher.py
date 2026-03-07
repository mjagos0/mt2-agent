from collections.abc import Callable
import logging

from .game_input import GameInputs, NUM_CHANNELS

logger = logging.getLogger(__name__)


class ChannelSwitcher:
    """Manages channel rotation state and executes channel-switch inputs."""

    def __init__(self, inputs: GameInputs, event_screenshot: Callable[[str], None]):
        self._inputs = inputs
        self._event_screenshot = event_screenshot
        self._current_idx: int = 0

    @property
    def current_channel(self) -> int:
        """Current channel number (1-indexed)."""
        return self._current_idx + 1

    def switch(self) -> None:
        next_idx = (self._current_idx + 1) % NUM_CHANNELS
        channel_input = self._inputs.channel_inputs[next_idx]

        logger.info(
            "Switching channel %d -> %d",
            self._current_idx + 1,
            next_idx + 1,
        )
        self._event_screenshot(f"channel-switch: {self._current_idx + 1} -> {next_idx + 1}")
        self._inputs.execute(channel_input, min_delay=0.3)
        self._current_idx = next_idx
