from .window_manager import Screenshot

import pytesseract
import numpy as np
import cv2
import re


def read_coordinates(screenshot: Screenshot) -> tuple[int, int] | None:
    gray = cv2.cvtColor(screenshot.data, cv2.COLOR_RGB2GRAY)
    gray = cv2.bitwise_not(gray)
    gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_LANCZOS4)
    _, bw = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)

    config = r'-c tessedit_char_whitelist=0123456789(), --psm 7'
    text = pytesseract.image_to_string(bw, config=config)

    match = re.search(r'\((\d+),\s*(\d+)\)', text)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None

def read_text(screenshot: Screenshot) -> str | None:
    gray = cv2.cvtColor(screenshot.data, cv2.COLOR_RGB2GRAY)
    gray = cv2.bitwise_not(gray)
    gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_LANCZOS4)
    _, bw = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)

    config = r'--psm 7'
    text = pytesseract.image_to_string(bw, config=config).strip()

    return text if text else None
