from .screenshot import Screenshot
from ..game_elements import GamePt, GameRec

import ctypes
import ctypes.wintypes as wt
import logging
import time

import bettercam

logger = logging.getLogger(__name__)

# Ideas:
# Cache resolution and cache and validate once per cycle, prevents calling windows API several times per cycle

class Window:
    window: wt.HWND
    camera: bettercam.BetterCam

    def __init__(self):
        self.camera = bettercam.create()

    def findWindow(self, class_name: str):
        logger.debug(f'Searching for window "{class_name}"')
        hwnd = ctypes.windll.user32.FindWindowW(class_name, None)
        if not hwnd:
            raise RuntimeError(f'Window with classa name {class_name} not found')
        else:
            self.window = hwnd
            logger.info(f'Attached to window "{hwnd}"')

        return hwnd
    
    def capture(self, gameRec: GameRec = None) -> Screenshot:
        if gameRec:
            x1, y1, x2, y2 = self.gamerec_to_screenrec(gameRec)
            region = (x1, y1, x2, y2)
        else:
            x, y = self.screenPt(0, 0)
            width, height = self.getResolution()
            screen_w = ctypes.windll.user32.GetSystemMetrics(0)
            screen_h = ctypes.windll.user32.GetSystemMetrics(1)
            region = (
                max(0, x),
                max(0, y),
                min(x + round(width * self.getScaleFactor()), screen_w),
                min(y + round(height * self.getScaleFactor()), screen_h)
            )

        logger.debug(f"Capturing region {region}")
        frame = self.camera.grab(region=region)
        if frame is None:
            raise RuntimeError("Failed to capture frame")
        logger.debug(f"Captured frame {frame.shape}")

        return Screenshot(
            data=frame,
            x_offset=region[0],
            y_offset=region[1]
        )
    
    def gamept_to_screenpt(self, gamePt: GamePt):
        width, height = self.getResolution()

        # WindowPt
        x = round(gamePt.widthAnchor() * width + gamePt.widthOffset)
        y = round(gamePt.heightAnchor() * height + gamePt.heightOffset)

        # ScreenPt
        return self.screenPt(x, y)
    
    def gamerec_to_screenrec(self, gameRec: GameRec):
        x, y = self.gamept_to_screenpt(gameRec)
        w = round(gameRec.width[0] * self.getScaleFactor())
        h = round(gameRec.height[1] * self.getScaleFactor())
        return (x, y, x + w, y + h)

    def screenPt(self, x: int, y: int) -> tuple[int, int]:
        pt = wt.POINT(round(x * self.scale), round(y * self.scale))
        ctypes.windll.user32.ClientToScreen(self.window, ctypes.byref(pt))
        
        return (pt.x, pt.y)
    
    def getResolution(self) -> tuple[int, int]:
        rect = wt.RECT()
        if not ctypes.windll.user32.GetClientRect(self.window, ctypes.byref(rect)):
            logger.error(f"Failed to get RECT of window {self.window}")

        return rect.right - rect.left, rect.bottom - rect.top
    
    def getScaleFactor(self) -> float:
        return ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
    
    def assertAlive(self):
        if not bool(ctypes.windll.user32.IsWindow(self.window)):
            logger.error(f'Window handle "{self.window}" is no longer valid')
            raise RuntimeError("Lost connection to window")
        else:
            logger.debug(f"Window {self.window} exists")
        
    def isFocused(self) -> bool:
        if (ctypes.windll.user32.GetForegroundWindow() == self.window):
            logger.debug(f"Window {self.window} is focused")
            return True
        else:
            logger.debug(f"Window {self.window} is not focused")
            return False
        
    def forceFocus(self, timeout: float = 2.0, interval: float = 0.05) -> bool:
        if not ctypes.windll.user32.SetForegroundWindow(self.window):
            logger.error(f'Failed to focus window "{self.window}"')
            return False

        start = time.perf_counter()
        while time.perf_counter() - start < timeout:
            if self.isFocused():
                return True
            time.sleep(interval)

        logger.error(f'Window "{self.window}" did not gain focus within {timeout}s')
        return False
