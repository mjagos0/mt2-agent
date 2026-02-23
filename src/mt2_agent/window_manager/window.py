from .screenshot import Screenshot

import ctypes
import ctypes.wintypes as wt

import logging
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
        origin = self.getPoint(0, 0)
        width, height = self.getDimensions()

        region = (origin.x, origin.y, origin.x + width, origin.y + height)
        logger.debug(f"Capturing region {region}")
        frame = self.camera.grab(region=region)
        if frame is None:
            raise RuntimeError("Failed to capture frame")
        logger.debug(f"Captured frame {frame.shape}")
        
        return Screenshot(
            data=frame,
            x_offset=origin.x,
            y_offset=origin.y
        )

    def getPoint(self, x: int, y: int) -> wt.POINT:
        pt = wt.POINT(x, y)
        ctypes.windll.user32.ClientToScreen(self.window, ctypes.byref(pt))

        return pt
    
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
        
    def forceFocus(self) -> bool:
        if not ctypes.windll.user32.SetForegroundWindow(self.window):
            logger.error(f'Failed to focus window "{self.window}"')
            return False
        return True
    

    

    
