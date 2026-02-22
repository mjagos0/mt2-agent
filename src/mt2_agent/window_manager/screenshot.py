from dataclasses import dataclass

@dataclass(frozen=True)
class Screenshot:
    image: bytes
    width: int
    height: int
    x_offset: int # Offset from left edge of the window
    y_offset: int # Offset from right edge of the window

    def __init__():
        ...
