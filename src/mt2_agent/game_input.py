from dataclasses import dataclass, field
from enum import Enum

import interception
from interception import beziercurve, MouseButton
import pytweening # type: ignore[import-untyped]
from typing import cast, Any

import math
import random
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
    tween=cast(Any, pytweening.linear),
    target_points=100,
)
BEZIER_PARAMS = beziercurve.BezierCurveParams()


@dataclass(frozen=True)
class FunctionKey:
    key: str


@dataclass(frozen=True)
class Click:
    key: MouseButton


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
    _min_action_delay: float = field(default=0.04, init=False)
    _delay_spread: float = field(default=0.02, init=False)
    _delay_sigma: float = field(default=0.5, init=False)

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

    LOGIN_1: Input = Input(keyboard=KeyboardInput("f1"))
    LOGIN_CONFIRM: Input = Input(keyboard=KeyboardInput("return"))

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

    def _random_delay(self, min_delay: float | None = None) -> float:
        gamma = min_delay if min_delay is not None else self._min_action_delay
        if self._delay_spread <= 0:
            return gamma

        sigma = self._delay_sigma
        mu = math.log(self._delay_spread) - (sigma ** 2) / 2

        return gamma + random.lognormvariate(mu, sigma)

    def _cooldown(self, min_delay: float | None = None):
        delay = self._random_delay(min_delay)
        if delay <= 0:
            return
        elapsed = time.monotonic() - self._last_action_time
        remaining = delay - elapsed
        if remaining > 0:
            time.sleep(remaining)
        self._last_action_time = time.monotonic()

    def click(
        self,
        pt: ScreenPt,
        button: MouseButton = "left",
        modifier: FunctionKey | None = None,
        movement: MovementType = MovementType.Instant,
        min_delay: float | None = None,
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
            min_delay=min_delay,
        )

    def move(
        self,
        pt: ScreenPt,
        movement: MovementType = MovementType.Instant,
        min_delay: float | None = None,
    ) -> None:
        self.execute(
            Input(
                mouse=MouseInput(
                    position=Position(pt, movement),
                )
            ),
            min_delay=min_delay,
        )

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

    def execute(
        self,
        input: Input,
        min_delay: float | None = None,
    ):
        if input.keyboard is not None:
            kb = input.keyboard
            assert kb.key is not None
            self._cooldown(min_delay)
            self._press_with_modifier(kb.key, kb.function_key)

        if input.mouse is not None:
            ms = input.mouse
            if ms.position is not None:
                self._cooldown(min_delay)
                self._move_mouse(ms.position)
            if ms.click is not None:
                self._cooldown(min_delay)
                if ms.function_key:
                    interception.key_down(ms.function_key.key)
                interception.click(button=ms.click.key)
                if ms.function_key:
                    interception.key_up(ms.function_key.key)