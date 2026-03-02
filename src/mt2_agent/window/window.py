from .screenshot import Screenshot
from .screen_objects import ScreenPt, ScreenRectangle
from ..game_ui import GamePt, GameRectangle

import ctypes
import ctypes.wintypes as wt
import logging
import time
import random

import bettercam  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


class Window:
    window: wt.HWND
    camera: bettercam.BetterCam

    def __init__(self) -> None:
        self.camera: bettercam.BetterCam = bettercam.create()  # type: ignore[reportUnknownMemberType]
        self.camera.start()  # type: ignore[reportUnknownMemberType]

    def findWindow(
        self, class_name: str | None = None, window_name: str | None = None
    ) -> wt.HWND:
        logger.debug(
            f'Searching for window (class="{class_name}", name="{window_name}")'
        )
        matches = self._enumerate_matching_windows(class_name, window_name)

        if not matches:
            raise RuntimeError(
                f'No window found matching class="{class_name}", name="{window_name}"'
            )
        elif len(matches) == 1:
            hwnd, cls, title = matches[0]
        else:
            print("Multiple matching windows found:")
            for i, (hwnd, cls, title) in enumerate(matches):
                print(f"  [{i}] {title!r} (class={cls!r}, hwnd={hwnd})")
            choice = int(input("Select window index: "))
            hwnd, cls, title = matches[choice]

        self.window = hwnd
        logger.info(f'Attached to window "{title}" (hwnd={hwnd})')
        return hwnd

    def capture(self, gameRec: GameRectangle | None = None) -> Screenshot:
        if gameRec is not None:
            rect = self.gamerec_to_screenrec(gameRec)
            region = rect.as_tuple()
        else:
            pt = self.screenPt(0, 0)
            width, height = self.getResolution()
            screen_w: int = ctypes.windll.user32.GetSystemMetrics(0)
            screen_h: int = ctypes.windll.user32.GetSystemMetrics(1)
            region = (
                max(0, pt.x),
                max(0, pt.y),
                min(pt.x + round(width * self.getScaleFactor()), screen_w),
                min(pt.y + round(height * self.getScaleFactor()), screen_h),
            )

        logger.debug(f"Capturing region {region}")
        frame = self.camera.get_latest_frame()

        # Crop the full-screen frame to the desired region
        x1, y1, x2, y2 = region
        frame = frame[y1:y2, x1:x2]

        logger.debug(f"Captured frame {frame.shape}")

        return Screenshot(data=frame, origin_x=region[0], origin_y=region[1])

    def random_point_from_center(self, t: float) -> ScreenPt:
        width, height = self.getGameResolution()
        cx, cy = width / 2, height / 2

        x = random.uniform(cx - (width * t) / 2, cx + (width * t) / 2)
        y = random.uniform(cy - (height * t) / 2, cy + (height * t) / 2)

        return self.screenPt(round(x), round(y))

    def gamept_to_screenpt(self, gamePt: GamePt) -> ScreenPt:
        width, height = self.getGameResolution()
        x = round(gamePt.widthAnchor * width + gamePt.widthOffset)
        y = round(gamePt.heightAnchor * height + gamePt.heightOffset)
        return self.screenPt(x, y)

    def gamerec_to_screenrec(self, gameRec: GameRectangle) -> ScreenRectangle:
        pt = self.gamept_to_screenpt(gameRec)
        w = round(gameRec.width * self.getScaleFactor())
        h = round(gameRec.height * self.getScaleFactor())
        return ScreenRectangle(pt.x, pt.y, pt.x + w, pt.y + h)

    def screenPt(self, x: int, y: int) -> ScreenPt:
        pt = wt.POINT(
            round(x * self.getScaleFactor()), round(y * self.getScaleFactor())
        )
        ctypes.windll.user32.ClientToScreen(self.window, ctypes.byref(pt))
        return ScreenPt(pt.x, pt.y)

    def getGameResolution(self) -> tuple[int, int]:
        w, h = self.getResolution()
        scale = self.getScaleFactor()
        return (round(w / scale), round(h / scale))

    def getResolution(self) -> tuple[int, int]:
        rect = wt.RECT()
        if not ctypes.windll.user32.GetClientRect(self.window, ctypes.byref(rect)):
            logger.error(f"Failed to get RECT of window {self.window}")

        return rect.right - rect.left, rect.bottom - rect.top

    def getScaleFactor(self) -> float:
        return ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100

    def assertAlive(self) -> None:
        if not bool(ctypes.windll.user32.IsWindow(self.window)):
            logger.error(f'Window handle "{self.window}" is no longer valid')
            raise RuntimeError("Lost connection to window")
        else:
            logger.debug(f"Window {self.window} exists")

    def isFocused(self) -> bool:
        if ctypes.windll.user32.GetForegroundWindow() == self.window:
            logger.debug(f"Window {self.window} is focused")
            return True
        else:
            logger.debug(f"Window {self.window} is not focused")
            return False

    def forceFocus(self, timeout: float = 2.0, poll_interval: float = 0.05) -> bool:
        if not ctypes.windll.user32.SetForegroundWindow(self.window):
            logger.error(f'Failed to focus window "{self.window}"')
            return False

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if ctypes.windll.user32.GetForegroundWindow() == self.window:
                logger.debug(f'Window brought forward "{self.window}"')
                return True
            time.sleep(poll_interval)

        logger.error(
            f'Timed out waiting for window "{self.window}" to become foreground'
        )
        return False

    def _enumerate_matching_windows(
        self, class_name: str | None = None, window_name: str | None = None
    ) -> list[tuple[wt.HWND, str, str]]:
        results: list[tuple[wt.HWND, str, str]] = []
        buf_size = 256

        @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
        def enum_cb(hwnd: wt.HWND, _: wt.LPARAM) -> bool:
            cls_buf = ctypes.create_unicode_buffer(buf_size)
            ctypes.windll.user32.GetClassNameW(hwnd, cls_buf, buf_size)
            cls = cls_buf.value

            title_buf = ctypes.create_unicode_buffer(buf_size)
            ctypes.windll.user32.GetWindowTextW(hwnd, title_buf, buf_size)
            title = title_buf.value

            class_ok = class_name is None or class_name.lower() in cls.lower()
            name_ok = window_name is None or window_name.lower() in title.lower()

            if class_ok and name_ok:
                results.append((hwnd, cls, title))
            return True

        ctypes.windll.user32.EnumWindows(enum_cb, 0)
        return results
