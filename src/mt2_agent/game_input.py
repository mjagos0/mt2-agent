from dataclasses import dataclass, field
from enum import Enum

import interception
from interception import beziercurve
import pytweening

import time

from .window import ScreenPt


class MovementType(Enum):
    Instant = 1
    Linear = 2
    Bezier = 3


LINEAR_PARAMS = beziercurve.BezierCurveParams(
    knots=0,
    distortion_mean=0,
    distortion_stdev=0,
    distortion_frequency=0,
    tween=pytweening.linear,
    target_points=100,
)
BEZIER_PARAMS = beziercurve.BezierCurveParams()


@dataclass(frozen=True)
class FunctionKey:
    key: str


@dataclass(frozen=True)
class Click:
    key: str


@dataclass(frozen=True)
class Position:
    coordinates: ScreenPt
    movementType: MovementType = MovementType.Instant


@dataclass(frozen=True)
class KeyboardInput:
    key: str | None
    function_key: FunctionKey | None = None


@dataclass(frozen=True)
class MouseInput:
    position: Position | None = None
    click: Click | None = None
    function_key: FunctionKey | None = None


@dataclass(frozen=True)
class Input:
    mouse: MouseInput | None = None
    keyboard: KeyboardInput | None = None


@dataclass
class GameInputs:
    min_action_delay: float
    _last_action_time: float = field(default=0.0, init=False)

    ESCAPE = FunctionKey("esc")
    CTRL = FunctionKey("ctrl")
    SHIFT = FunctionKey("shift")
    CLICK_LEFT = Click("left")
    CLICK_RIGHT = Click("right")

    # Hotkeys
    HOTKEY_1: Input = Input(keyboard=KeyboardInput("1"))
    HOTKEY_2: Input = Input(keyboard=KeyboardInput("2"))
    HOTKEY_3: Input = Input(keyboard=KeyboardInput("3"))
    HOTKEY_4: Input = Input(keyboard=KeyboardInput("4"))

    HOTKEY_F1: Input = Input(keyboard=KeyboardInput("f1"))
    HOTKEY_F2: Input = Input(keyboard=KeyboardInput("f2"))
    HOTKEY_F3: Input = Input(keyboard=KeyboardInput("f3"))
    HOTKEY_F4: Input = Input(keyboard=KeyboardInput("f4"))

    PICKUP_ITEMS: Input = Input(keyboard=KeyboardInput("z"))
    TOGGLE_HORSE: Input = Input(keyboard=KeyboardInput("h", CTRL))
    BRAVERY_CAPE: Input = HOTKEY_1

    # Mouse-only actions
    LEFT_CLICK: Input = Input(mouse=MouseInput(click=CLICK_LEFT))
    RIGHT_CLICK: Input = Input(mouse=MouseInput(click=CLICK_RIGHT))

    # Nothyr
    DROP_METIN_QUEUE: Input = Input()
    OPEN_BIOLOG_KEY: Input = Input()

    @property
    def hotkeys(self) -> list[Input]:
        return [
            self.HOTKEY_1,
            self.HOTKEY_2,
            self.HOTKEY_3,
            self.HOTKEY_4,
            self.HOTKEY_F1,
            self.HOTKEY_F2,
            self.HOTKEY_F3,
            self.HOTKEY_F4,
        ]

    def click(
        self,
        pt: ScreenPt,
        button: str = "left",
        modifier: FunctionKey | None = None,
        movement: MovementType = MovementType.Instant,
        extra_delay: float = 0.0,
    ) -> None:
        click = Click(button)
        self.execute(
            Input(
                mouse=MouseInput(
                    position=Position(pt, movement),
                    click=click,
                    function_key=modifier,
                )
            ),
            extra_delay,
        )

    def move(
        self,
        pt: ScreenPt,
        movement: MovementType = MovementType.Instant,
        extra_delay: float = 0.0,
    ) -> None:
        self.execute(
            Input(
                mouse=MouseInput(
                    position=Position(pt, movement),
                )
            ),
            extra_delay,
        )

    def _cooldown(self, extra_delay: float):
        if self.min_action_delay <= 0:
            return
        elapsed = time.monotonic() - self._last_action_time
        remaining = self.min_action_delay + extra_delay - elapsed
        if remaining > 0:
            time.sleep(remaining)
        self._last_action_time = time.monotonic()

    def _move_mouse(self, position: Position):
        x, y = position.coordinates.as_tuple()
        match position.movementType:
            case MovementType.Instant:
                interception.move_to(x, y)
            case MovementType.Linear:
                interception.move_to(x, y, LINEAR_PARAMS)
            case MovementType.Bezier:
                interception.move_to(x, y, BEZIER_PARAMS)

    def _press_with_modifier(self, key: str, fc_key: FunctionKey | None):
        if fc_key:
            interception.key_down(fc_key.key)
        interception.press(key)
        if fc_key:
            interception.key_up(fc_key.key)

    def execute(self, input: Input, extra_delay: float = 0.0):
        if input.keyboard is not None:
            kb = input.keyboard
            assert kb.key is not None
            self._cooldown(extra_delay)
            self._press_with_modifier(kb.key, kb.function_key)

        if input.mouse is not None:
            ms = input.mouse
            if ms.position is not None:
                self._cooldown(extra_delay)
                self._move_mouse(ms.position)
            if ms.click is not None:
                self._cooldown(extra_delay)
                if ms.function_key:
                    interception.key_down(ms.function_key.key)
                interception.click(button=ms.click.key)
                if ms.function_key:
                    interception.key_up(ms.function_key.key)
