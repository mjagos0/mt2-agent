from .screenshot import Screenshot

import ctypes
import ctypes.wintypes as wt
import logging
import time

import bettercam

logger = logging.getLogger(__name__)

class Window:
    window: wt.HWND
    camera: bettercam.BetterCam

    def __init__(self, window_class_name: str, expected_window_name: str):
        self.window = self.findWindow(window_class_name, expected_window_name)
        self.camera = bettercam.create()

    def findWindow(self, class_name: str, expected_window_name: str):
        logger.debug(f'Searching for window "{class_name}"')
        hwnd = ctypes.windll.user32.FindWindowW(class_name, None)
        if not hwnd:
            logger.error(f'Window "{class_name}" not found')
            raise RuntimeError(f'{expected_window_name} window not found')

        logger.info(f'Attached to window "{hwnd}"')

        return hwnd
    
    def capture(self) -> Screenshot:
        x, y = self.windowPoint(0, 0)
        width, height = self.getDimensions()

        screen_w = ctypes.windll.user32.GetSystemMetrics(0)
        screen_h = ctypes.windll.user32.GetSystemMetrics(1)

        region = (
            max(0, x),
            max(0, y),
            min(x + width, screen_w),
            min(y + height, screen_h)
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

    def windowPoint(self, x: int, y: int) -> tuple[int, int]:
        pt = wt.POINT(x, y)
        ctypes.windll.user32.ClientToScreen(self.window, ctypes.byref(pt))

        return (pt.x, pt.y)
    
    def getDimensions(self) -> tuple[int, int]:
        rect = self.getRect()
        return rect.right - rect.left, rect.bottom - rect.top
    
    def getRect(self) -> wt.RECT:
        rect = wt.RECT()
        if not ctypes.windll.user32.GetClientRect(self.window, ctypes.byref(rect)):
            logger.error(f"Failed to get RECT of window {self.window}")
        
        return rect
    
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
