from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import interception
from interception import MouseButton
import pytweening  # type: ignore[import-untyped]

import math
import random
import time

from .window import ScreenPt


class MovementType(Enum):
    Instant = 1
    Linear = 2
    Bezier = 3


# ---------------------------------------------------------------------------
# Custom point-interpolation helpers
# ---------------------------------------------------------------------------
# These replace interception's built-in bezier/linear movement so that we
# only ever call `interception.move_to(x, y)` (the instant warp), which does
# NOT activate the Windows "enhance pointer precision" setting.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CurveParams:
    """Parameters that control human-like mouse curves."""

    # Number of random internal control points (knots) for bezier curves.
    # 0 = straight line with only tweening applied.
    knots: int = 2

    # How far (in pixels) knots may deviate from the straight line.
    distortion_mean: float = 1.0
    distortion_stdev: float = 1.0
    distortion_frequency: float = 0.5

    # Tweening function applied to the parametric t ∈ [0, 1].
    tween: Any = pytweening.easeOutQuad

    # How many discrete steps the curve is split into.
    target_points: int = 80

    # Base seconds between each step (randomised a bit).
    step_delay: float = 0.002


LINEAR_CURVE = CurveParams(
    knots=0,
    distortion_mean=0,
    distortion_stdev=0,
    distortion_frequency=0,
    tween=pytweening.linear,
    target_points=100,
    step_delay=0.002,
)

BEZIER_CURVE = CurveParams()


def _bernstein_basis(n: int, i: int, t: float) -> float:
    """Bernstein basis polynomial B_{i,n}(t)."""
    return math.comb(n, i) * (t ** i) * ((1 - t) ** (n - i))


def _evaluate_bezier(control_points: list[tuple[float, float]], t: float) -> tuple[float, float]:
    """Evaluate a bezier curve defined by *control_points* at parameter *t*."""
    n = len(control_points) - 1
    x = sum(_bernstein_basis(n, i, t) * p[0] for i, p in enumerate(control_points))
    y = sum(_bernstein_basis(n, i, t) * p[1] for i, p in enumerate(control_points))
    return (x, y)


def _generate_internal_knots(
    start: tuple[float, float],
    end: tuple[float, float],
    params: CurveParams,
) -> list[tuple[float, float]]:
    """Generate random internal knots between *start* and *end*."""
    if params.knots <= 0:
        return []

    knots: list[tuple[float, float]] = []
    for i in range(1, params.knots + 1):
        frac = i / (params.knots + 1)
        mid_x = start[0] + (end[0] - start[0]) * frac
        mid_y = start[1] + (end[1] - start[1]) * frac

        if params.distortion_mean > 0 or params.distortion_stdev > 0:
            if random.random() < params.distortion_frequency:
                offset_x = random.gauss(0, params.distortion_mean + params.distortion_stdev)
                offset_y = random.gauss(0, params.distortion_mean + params.distortion_stdev)
                mid_x += offset_x
                mid_y += offset_y

        knots.append((mid_x, mid_y))
    return knots


def generate_curve_points(
    from_pt: tuple[float, float],
    to_pt: tuple[float, float],
    params: CurveParams,
) -> list[tuple[int, int]]:
    """
    Return a list of integer (x, y) screen coordinates tracing a curve from
    *from_pt* to *to_pt* according to *params*.

    The tweening function is applied to the parametric variable so that
    acceleration / deceleration is baked into the spacing of points.
    """
    control_points: list[tuple[float, float]] = [
        from_pt,
        *_generate_internal_knots(from_pt, to_pt, params),
        to_pt,
    ]

    n_steps = max(params.target_points, 2)
    points: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()

    for step in range(n_steps + 1):
        raw_t = step / n_steps
        t = params.tween(raw_t) if params.tween else raw_t
        t = max(0.0, min(1.0, t))

        fx, fy = _evaluate_bezier(control_points, t)
        pt = (int(round(fx)), int(round(fy)))

        # Deduplicate consecutive identical pixel positions.
        if pt not in seen:
            points.append(pt)
            seen.add(pt)

    # Always ensure we end exactly on the target.
    target = (int(round(to_pt[0])), int(round(to_pt[1])))
    if not points or points[-1] != target:
        points.append(target)

    return points


# ---------------------------------------------------------------------------
# Dataclasses for input abstraction
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Main GameInputs controller
# ---------------------------------------------------------------------------


@dataclass
class GameInputs:
    _min_action_delay: float = field(default=0.08, init=False)
    _delay_spread: float = field(default=0.03, init=False)
    _delay_sigma: float = field(default=0.5, init=False)

    _last_action_time: float = field(default=0.0, init=False)

    # We track the last position ourselves since interception has no getter.
    _last_mouse_pos: tuple[int, int] = field(default=(0, 0), init=False)

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
    CLOSE_WINDOW: Input = Input(keyboard=KeyboardInput("esc"))

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

    # -----------------------------------------------------------------------
    # Delay / cooldown helpers
    # -----------------------------------------------------------------------

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

    # -----------------------------------------------------------------------
    # Public convenience methods
    # -----------------------------------------------------------------------

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

    # -----------------------------------------------------------------------
    # Mouse movement – always uses instant move_to under the hood
    # -----------------------------------------------------------------------

    def _move_mouse(self, position: Position):
        x, y = position.coordinates.as_tuple()

        match position.movementType:
            case MovementType.Instant:
                interception.move_to(x, y)
            case MovementType.Linear:
                self._interpolated_move(x, y, LINEAR_CURVE)
            case MovementType.Bezier:
                self._interpolated_move(x, y, BEZIER_CURVE)

        self._last_mouse_pos = (x, y)

    def _interpolated_move(self, target_x: int, target_y: int, params: CurveParams):
        from_pt = (float(self._last_mouse_pos[0]), float(self._last_mouse_pos[1]))
        to_pt = (float(target_x), float(target_y))

        points = generate_curve_points(from_pt, to_pt, params)

        for px, py in points:
            interception.move_to(px, py)
            # Small random jitter on the delay keeps the movement organic.
            jitter = random.uniform(0.5, 1.5)
            time.sleep(params.step_delay * jitter)

    # -----------------------------------------------------------------------
    # Keyboard helpers
    # -----------------------------------------------------------------------

    def _press_with_modifier(self, key: str, fc_key: FunctionKey | None):
        if fc_key:
            interception.key_down(fc_key.key)
        interception.press(key)
        if fc_key:
            interception.key_up(fc_key.key)

    # -----------------------------------------------------------------------
    # Main execute entry-point
    # -----------------------------------------------------------------------

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