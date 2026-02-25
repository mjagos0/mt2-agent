from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union

NAMED_ANCHORS = {
    "top-left":      (0.0, 0.0),
    "top-right":     (1.0, 0.0),
    "bottom-left":   (0.0, 1.0),
    "bottom-right":  (1.0, 1.0),
    "center":        (0.5, 0.5),
}

BIOLOG_CONFIRM_ANCHOR = NAMED_ANCHORS["center"]
BIOLOG_CONFIRM_OFFSET = (15.5, -114.5)

BIOLOG_SHOP_ANCHOR = NAMED_ANCHORS["center"]
BIOLOG_SHOP_OFFSET = (102, -69.5)

ORC_TOOTH_ANCHOR = (2/3, 0.0)
ORC_TOOTH_OFFSET = (196.33, 249)


@dataclass
class UIElement:
    anchor: Union[str, tuple[float, float]]
    offset: tuple[float, float]

    @property
    def ratios(self) -> tuple[float, float]:
        if isinstance(self.anchor, str):
            return NAMED_ANCHORS[self.anchor]
        return self.anchor

    def get_position(self, width: int, height: int) -> tuple[int, int]:
        rx, ry = self.ratios
        x = round(rx * width + self.offset[0])
        y = round(ry * height + self.offset[1])
        return (x, y)

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self  # class-level access returns the descriptor itself
        return self.get_position(obj.width, obj.height)


class NothyrUI:
    biolog_confirm = UIElement(BIOLOG_CONFIRM_ANCHOR, BIOLOG_CONFIRM_OFFSET)
    biolog_shop = UIElement(BIOLOG_SHOP_ANCHOR, BIOLOG_SHOP_OFFSET)
    orc_tooth = UIElement(ORC_TOOTH_ANCHOR, ORC_TOOTH_OFFSET)

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
