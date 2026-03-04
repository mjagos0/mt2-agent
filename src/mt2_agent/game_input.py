from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

import ctypes
import ctypes.wintypes
import pytweening  # type: ignore[import-untyped]

import math
import random
import time

from .window import ScreenPt


# ---------------------------------------------------------------------------
# Win32 SendInput structures and constants
# ---------------------------------------------------------------------------

user32 = ctypes.windll.user32

# Input type constants
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

# Mouse event flags
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_ABSOLUTE = 0x8000

# Keyboard event flags
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002

# Screen metrics for absolute mouse coordinates
SM_CXSCREEN = 0
SM_CYSCREEN = 1


# --- C structures for SendInput ---

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.wintypes.LONG),
        ("dy", ctypes.wintypes.LONG),
        ("mouseData", ctypes.wintypes.DWORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.wintypes.WORD),
        ("wScan", ctypes.wintypes.WORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", ctypes.wintypes.DWORD),
        ("wParamL", ctypes.wintypes.WORD),
        ("wParamH", ctypes.wintypes.WORD),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.wintypes.DWORD),
        ("union", _INPUT_UNION),
    ]


# ---------------------------------------------------------------------------
# Scan code table – hardware scan codes for Set 1 (XT)
# ---------------------------------------------------------------------------

SCAN_CODE_MAP: dict[str, int] = {
    # Row 0 – Escape / Function keys
    "esc": 0x01, "escape": 0x01,
    "f1": 0x3B, "f2": 0x3C, "f3": 0x3D, "f4": 0x3E,
    "f5": 0x3F, "f6": 0x40, "f7": 0x41, "f8": 0x42,
    "f9": 0x43, "f10": 0x44, "f11": 0x57, "f12": 0x58,

    # Row 1 – Number row
    "`": 0x29, "1": 0x02, "2": 0x03, "3": 0x04, "4": 0x05,
    "5": 0x06, "6": 0x07, "7": 0x08, "8": 0x09, "9": 0x0A,
    "0": 0x0B, "-": 0x0C, "=": 0x0D, "backspace": 0x0E,

    # Row 2
    "tab": 0x0F,
    "q": 0x10, "w": 0x11, "e": 0x12, "r": 0x13, "t": 0x14,
    "y": 0x15, "u": 0x16, "i": 0x17, "o": 0x18, "p": 0x19,
    "[": 0x1A, "]": 0x1B, "\\": 0x2B,

    # Row 3
    "capslock": 0x3A,
    "a": 0x1E, "s": 0x1F, "d": 0x20, "f": 0x21, "g": 0x22,
    "h": 0x23, "j": 0x24, "k": 0x25, "l": 0x26,
    ";": 0x27, "'": 0x28,
    "return": 0x1C, "enter": 0x1C,

    # Row 4
    "shift": 0x2A, "lshift": 0x2A,
    "z": 0x2C, "x": 0x2D, "c": 0x2E, "v": 0x2F, "b": 0x30,
    "n": 0x31, "m": 0x32, ",": 0x33, ".": 0x34, "/": 0x35,
    "rshift": 0x36,

    # Row 5
    "ctrl": 0x1D, "lctrl": 0x1D,
    "alt": 0x38, "lalt": 0x38,
    "space": 0x39,

    # Arrow keys (extended – handled specially)
    "up": 0x48, "down": 0x50, "left": 0x4B, "right": 0x4D,

    # Misc
    "insert": 0x52, "delete": 0x53,
    "home": 0x47, "end": 0x4F,
    "pageup": 0x49, "pagedown": 0x51,
}

# Keys that require the extended flag (0xE0 prefix in scan-code set 1).
_EXTENDED_KEYS = {
    "up", "down", "left", "right",
    "insert", "delete", "home", "end", "pageup", "pagedown",
    "rctrl", "ralt",
}


# ---------------------------------------------------------------------------
# Low-level send helpers
# ---------------------------------------------------------------------------

def _send_inputs(*inputs: INPUT) -> int:
    """Call SendInput for one or more INPUT structs."""
    arr = (INPUT * len(inputs))(*inputs)
    return user32.SendInput(len(arr), arr, ctypes.sizeof(INPUT))


def _make_key_input(scan_code: int, flags: int) -> INPUT:
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.union.ki.wVk = 0
    inp.union.ki.wScan = scan_code
    inp.union.ki.dwFlags = flags
    inp.union.ki.time = 0
    inp.union.ki.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
    return inp


def _key_flags(key_name: str, up: bool = False) -> int:
    flags = KEYEVENTF_SCANCODE
    if key_name.lower() in _EXTENDED_KEYS:
        flags |= 0x0001  # KEYEVENTF_EXTENDEDKEY
    if up:
        flags |= KEYEVENTF_KEYUP
    return flags


def _resolve_scan_code(key_name: str) -> int:
    code = SCAN_CODE_MAP.get(key_name.lower())
    if code is None:
        raise ValueError(f"Unknown key name: {key_name!r}")
    return code


def _key_down(key: str) -> None:
    sc = _resolve_scan_code(key)
    _send_inputs(_make_key_input(sc, _key_flags(key, up=False)))


def _key_up(key: str) -> None:
    sc = _resolve_scan_code(key)
    _send_inputs(_make_key_input(sc, _key_flags(key, up=True)))


def _press(key: str) -> None:
    """Press and release a key via scan code."""
    sc = _resolve_scan_code(key)
    down = _make_key_input(sc, _key_flags(key, up=False))
    up = _make_key_input(sc, _key_flags(key, up=True))
    _send_inputs(down, up)


# ---------------------------------------------------------------------------
# Mouse helpers
# ---------------------------------------------------------------------------

def _screen_size() -> tuple[int, int]:
    return user32.GetSystemMetrics(SM_CXSCREEN), user32.GetSystemMetrics(SM_CYSCREEN)


def _abs_coords(x: int, y: int) -> tuple[int, int]:
    """Convert pixel coordinates to the 0-65535 normalised range for MOUSEEVENTF_ABSOLUTE."""
    cx, cy = _screen_size()
    # The formula matches Windows convention: (pixel + 0.5) / screen * 65536
    norm_x = int((x * 65536 + cx // 2) / cx)
    norm_y = int((y * 65536 + cy // 2) / cy)
    return norm_x, norm_y


def _move_to(x: int, y: int) -> None:
    """Instantly warp the cursor to (x, y) screen coordinates."""
    nx, ny = _abs_coords(x, y)
    inp = INPUT()
    inp.type = INPUT_MOUSE
    inp.union.mi.dx = nx
    inp.union.mi.dy = ny
    inp.union.mi.mouseData = 0
    inp.union.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
    inp.union.mi.time = 0
    inp.union.mi.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
    _send_inputs(inp)


def _mouse_click(button: str = "left") -> None:
    """Click (press + release) a mouse button at the current cursor position."""
    if button == "left":
        down_flag, up_flag = MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP
    elif button == "right":
        down_flag, up_flag = MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP
    elif button == "middle":
        down_flag, up_flag = MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP
    else:
        raise ValueError(f"Unknown mouse button: {button!r}")

    down_inp = INPUT()
    down_inp.type = INPUT_MOUSE
    down_inp.union.mi.dwFlags = down_flag
    down_inp.union.mi.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))

    up_inp = INPUT()
    up_inp.type = INPUT_MOUSE
    up_inp.union.mi.dwFlags = up_flag
    up_inp.union.mi.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))

    _send_inputs(down_inp, up_inp)


# ---------------------------------------------------------------------------
# Type alias to keep the public interface identical
# ---------------------------------------------------------------------------

MouseButton = Literal["left", "right", "middle"]


# ---------------------------------------------------------------------------
# Movement types & curve helpers (unchanged logic)
# ---------------------------------------------------------------------------

class MovementType(Enum):
    Instant = 1
    Linear = 2
    Bezier = 3


@dataclass(frozen=True)
class CurveParams:
    """Parameters that control human-like mouse curves."""
    knots: int = 2
    distortion_mean: float = 1.0
    distortion_stdev: float = 1.0
    distortion_frequency: float = 0.5
    tween: Any = pytweening.easeOutQuad
    target_points: int = 80
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
    return math.comb(n, i) * (t ** i) * ((1 - t) ** (n - i))


def _evaluate_bezier(control_points: list[tuple[float, float]], t: float) -> tuple[float, float]:
    n = len(control_points) - 1
    x = sum(_bernstein_basis(n, i, t) * p[0] for i, p in enumerate(control_points))
    y = sum(_bernstein_basis(n, i, t) * p[1] for i, p in enumerate(control_points))
    return (x, y)


def _generate_internal_knots(
    start: tuple[float, float],
    end: tuple[float, float],
    params: CurveParams,
) -> list[tuple[float, float]]:
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

        if pt not in seen:
            points.append(pt)
            seen.add(pt)

    target = (int(round(to_pt[0])), int(round(to_pt[1])))
    if not points or points[-1] != target:
        points.append(target)

    return points


# ---------------------------------------------------------------------------
# Dataclasses for input abstraction (unchanged public interface)
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
    TOGGLE_INVENTORY: Input = Input(keyboard=KeyboardInput("i"))
    CLOSE_WINDOW: Input = Input(keyboard=KeyboardInput("esc"))
    ATTACK_BUTTON: Input = Input(keyboard=KeyboardInput("space"))

    @property
    def hotkeys(self) -> list[Input]:
        return [
            self.HOTKEY_1, self.HOTKEY_2, self.HOTKEY_3, self.HOTKEY_4,
            self.HOTKEY_F1, self.HOTKEY_F2, self.HOTKEY_F3, self.HOTKEY_F4,
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
        click_obj = Click(button)
        self.execute(
            Input(
                mouse=MouseInput(
                    position=Position(pt, movement),
                    click=click_obj,
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
    # Mouse movement – uses SendInput MOUSEEVENTF_ABSOLUTE under the hood
    # -----------------------------------------------------------------------

    def _move_mouse(self, position: Position):
        x, y = position.coordinates.as_tuple()

        match position.movementType:
            case MovementType.Instant:
                _move_to(x, y)
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
            _move_to(px, py)
            jitter = random.uniform(0.5, 1.5)
            time.sleep(params.step_delay * jitter)

    # -----------------------------------------------------------------------
    # Keyboard helpers
    # -----------------------------------------------------------------------

    def _press_with_modifier(self, key: str, fc_key: FunctionKey | None):
        if fc_key:
            _key_down(fc_key.key)
        _press(key)
        if fc_key:
            _key_up(fc_key.key)

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
                    _key_down(ms.function_key.key)
                _mouse_click(button=ms.click.key)
                if ms.function_key:
                    _key_up(ms.function_key.key)

    def toggle_key(
            self,
            input: Input,
            hold: bool = True
    ):
        if input.keyboard is not None and input.keyboard.key is not None:
            if hold:
                _key_down(input.keyboard.key)
            else:
                _key_up(input.keyboard.key)