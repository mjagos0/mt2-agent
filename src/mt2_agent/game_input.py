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

user32 = ctypes.windll.user32  # type: ignore[attr-defined]

# Input type constants
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

# Keyboard event flags (for SendInput — used only as fallback reference)
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001

# Mouse event flags
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_ABSOLUTE = 0x8000

# Screen metrics
SM_CXSCREEN = 0
SM_CYSCREEN = 1

# Window messages for keyboard
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101

# MapVirtualKeyW mapping type: scan code -> virtual key
MAPVK_VSC_TO_VK = 1
MAPVK_VSC_TO_VK_EX = 3


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
# Scan-code lookup table  (Set 1 / AT scan codes)
# ---------------------------------------------------------------------------

_SCAN_CODES: dict[str, tuple[int, bool]] = {
    # Number row
    "1": (0x02, False),
    "2": (0x03, False),
    "3": (0x04, False),
    "4": (0x05, False),
    "5": (0x06, False),
    "6": (0x07, False),
    "7": (0x08, False),
    "8": (0x09, False),
    "9": (0x0A, False),
    "0": (0x0B, False),

    # Letters (QWERTY)
    "q": (0x10, False),
    "w": (0x11, False),
    "e": (0x12, False),
    "r": (0x13, False),
    "t": (0x14, False),
    "y": (0x15, False),
    "u": (0x16, False),
    "i": (0x17, False),
    "o": (0x18, False),
    "p": (0x19, False),
    "a": (0x1E, False),
    "s": (0x1F, False),
    "d": (0x20, False),
    "f": (0x21, False),
    "g": (0x22, False),
    "h": (0x23, False),
    "j": (0x24, False),
    "k": (0x25, False),
    "l": (0x26, False),
    "z": (0x2C, False),
    "x": (0x2D, False),
    "c": (0x2E, False),
    "v": (0x2F, False),
    "b": (0x30, False),
    "n": (0x31, False),
    "m": (0x32, False),

    # Special keys
    "esc": (0x01, False),
    "escape": (0x01, False),
    "return": (0x1C, False),
    "enter": (0x1C, False),
    "space": (0x39, False),
    "tab": (0x0F, False),
    "backspace": (0x0E, False),

    # Modifiers
    "shift": (0x2A, False),
    "lshift": (0x2A, False),
    "rshift": (0x36, False),
    "ctrl": (0x1D, False),
    "lctrl": (0x1D, False),
    "rctrl": (0x1D, True),
    "alt": (0x38, False),
    "lalt": (0x38, False),
    "ralt": (0x38, True),

    # Function keys
    "f1": (0x3B, False),
    "f2": (0x3C, False),
    "f3": (0x3D, False),
    "f4": (0x3E, False),
    "f5": (0x3F, False),
    "f6": (0x40, False),
    "f7": (0x41, False),
    "f8": (0x42, False),
    "f9": (0x43, False),
    "f10": (0x44, False),
    "f11": (0x57, False),
    "f12": (0x58, False),

    # Arrow keys (extended)
    "up": (0x48, True),
    "down": (0x50, True),
    "left": (0x4B, True),
    "right": (0x4D, True),

    # Navigation cluster (extended)
    "insert": (0x52, True),
    "delete": (0x53, True),
    "home": (0x47, True),
    "end": (0x4F, True),
    "pageup": (0x49, True),
    "pagedown": (0x51, True),
}


def _resolve_scan(key: str) -> tuple[int, bool]:
    """Look up the scan code and extended flag for a key name."""
    lower = key.lower()
    if lower not in _SCAN_CODES:
        raise ValueError(f"Unknown key name: {key!r} – add it to _SCAN_CODES")
    return _SCAN_CODES[lower]


# ---------------------------------------------------------------------------
# Mouse helpers (SendInput – works fine, games don't filter mouse)
# ---------------------------------------------------------------------------

def _send_inputs(*inputs: INPUT) -> int:
    arr = (INPUT * len(inputs))(*inputs)
    return user32.SendInput(len(arr), arr, ctypes.sizeof(INPUT))


def _screen_size() -> tuple[int, int]:
    return (
        user32.GetSystemMetrics(SM_CXSCREEN),
        user32.GetSystemMetrics(SM_CYSCREEN),
    )


def move_to(x: int, y: int) -> None:
    """Move the mouse cursor to absolute screen pixel coordinates."""
    cx, cy = _screen_size()
    abs_x = int(x * 65536 / cx)
    abs_y = int(y * 65536 / cy)

    mi = MOUSEINPUT(
        dx=abs_x,
        dy=abs_y,
        mouseData=0,
        dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE,
        time=0,
        dwExtraInfo=ctypes.pointer(ctypes.c_ulong(0)),
    )
    inp = INPUT(type=INPUT_MOUSE)
    inp.union.mi = mi
    _send_inputs(inp)


def mouse_click(button: str = "left") -> None:
    """Click a mouse button at the current cursor position via SendInput."""
    if button == "left":
        down_flag, up_flag = MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP
    elif button == "right":
        down_flag, up_flag = MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP
    elif button == "middle":
        down_flag, up_flag = MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP
    else:
        raise ValueError(f"Unsupported mouse button: {button!r}")

    mi_down = MOUSEINPUT(
        dx=0, dy=0, mouseData=0, dwFlags=down_flag, time=0,
        dwExtraInfo=ctypes.pointer(ctypes.c_ulong(0)),
    )
    mi_up = MOUSEINPUT(
        dx=0, dy=0, mouseData=0, dwFlags=up_flag, time=0,
        dwExtraInfo=ctypes.pointer(ctypes.c_ulong(0)),
    )
    inp_down = INPUT(type=INPUT_MOUSE)
    inp_down.union.mi = mi_down
    inp_up = INPUT(type=INPUT_MOUSE)
    inp_up.union.mi = mi_up
    _send_inputs(inp_down, inp_up)


# ---------------------------------------------------------------------------
# Keyboard helpers (PostMessage – no LLKHF_INJECTED flag)
# ---------------------------------------------------------------------------
# WM_KEYDOWN / WM_KEYUP lParam layout:
#   Bits  0-15 : repeat count (1)
#   Bits 16-23 : scan code
#   Bit  24    : extended key flag
#   Bits 25-28 : reserved (0)
#   Bit  29    : context code (0 for WM_KEYDOWN/UP)
#   Bit  30    : previous key state (0 = was up for DOWN, 1 = was down for UP)
#   Bit  31    : transition state (0 = being pressed, 1 = being released)
# ---------------------------------------------------------------------------

def _make_lparam(scan_code: int, extended: bool, key_up: bool) -> int:
    """Build the lParam for WM_KEYDOWN / WM_KEYUP."""
    lparam = 1  # repeat count = 1
    lparam |= (scan_code & 0xFF) << 16
    if extended:
        lparam |= 1 << 24
    if key_up:
        lparam |= 1 << 30  # previous key state = was down
        lparam |= 1 << 31  # transition state = being released
    return lparam


def _scan_to_vk(scan_code: int, extended: bool) -> int:
    """Convert a scan code to a virtual key code via MapVirtualKeyW."""
    # For extended keys, use MAPVK_VSC_TO_VK_EX which distinguishes
    # e.g. left ctrl vs right ctrl.
    map_type = MAPVK_VSC_TO_VK_EX if extended else MAPVK_VSC_TO_VK
    vk = user32.MapVirtualKeyW(scan_code, map_type)
    return vk


def _post_key(hwnd: ctypes.wintypes.HWND, scan_code: int, extended: bool, key_up: bool) -> None:
    """Post a single WM_KEYDOWN or WM_KEYUP to the target window."""
    vk = _scan_to_vk(scan_code, extended)
    msg = WM_KEYUP if key_up else WM_KEYDOWN
    lparam = _make_lparam(scan_code, extended, key_up)
    user32.PostMessageW(hwnd, msg, vk, lparam)


def post_key_down(hwnd: ctypes.wintypes.HWND, key: str) -> None:
    scan, ext = _resolve_scan(key)
    _post_key(hwnd, scan, ext, key_up=False)


def post_key_up(hwnd: ctypes.wintypes.HWND, key: str) -> None:
    scan, ext = _resolve_scan(key)
    _post_key(hwnd, scan, ext, key_up=True)


def post_press(hwnd: ctypes.wintypes.HWND, key: str) -> None:
    """Full key press: WM_KEYDOWN then WM_KEYUP."""
    scan, ext = _resolve_scan(key)
    _post_key(hwnd, scan, ext, key_up=False)
    _post_key(hwnd, scan, ext, key_up=True)


# ---------------------------------------------------------------------------
# Type alias replacing interception.MouseButton
# ---------------------------------------------------------------------------

MouseButton = Literal["left", "right", "middle"]


class MovementType(Enum):
    Instant = 1
    Linear = 2
    Bezier = 3


# ---------------------------------------------------------------------------
# Custom point-interpolation helpers
# ---------------------------------------------------------------------------


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

    # We track the last position ourselves since SendInput has no getter.
    _last_mouse_pos: tuple[int, int] = field(default=(0, 0), init=False)

    # Window handle for PostMessage keyboard input.
    # Set after construction by GameInterface.__init__().
    _hwnd: ctypes.wintypes.HWND = field(default=ctypes.wintypes.HWND(0), init=False)

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

    def set_hwnd(self, hwnd: ctypes.wintypes.HWND) -> None:
        """Bind this input controller to a game window handle."""
        self._hwnd = hwnd

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
    # Mouse movement – always uses instant move_to under the hood
    # -----------------------------------------------------------------------

    def _move_mouse(self, position: Position):
        x, y = position.coordinates.as_tuple()

        match position.movementType:
            case MovementType.Instant:
                move_to(x, y)
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
            move_to(px, py)
            jitter = random.uniform(0.5, 1.5)
            time.sleep(params.step_delay * jitter)

    # -----------------------------------------------------------------------
    # Keyboard helpers – PostMessage to game window
    # -----------------------------------------------------------------------

    def _press_with_modifier(self, key: str, fc_key: FunctionKey | None):
        hwnd = self._hwnd
        if fc_key:
            post_key_down(hwnd, fc_key.key)
        post_press(hwnd, key)
        if fc_key:
            post_key_up(hwnd, fc_key.key)

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
                    post_key_down(self._hwnd, ms.function_key.key)
                mouse_click(button=ms.click.key)
                if ms.function_key:
                    post_key_up(self._hwnd, ms.function_key.key)

    def toggle_key(
            self,
            input: Input,
            hold: bool = True
    ):
        if input.keyboard is not None and input.keyboard.key is not None:
            if hold:
                post_key_down(self._hwnd, input.keyboard.key)
            else:
                post_key_up(self._hwnd, input.keyboard.key)