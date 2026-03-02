from dataclasses import dataclass


@dataclass(frozen=True)
class ScreenPt:
    x: int
    y: int

    def as_tuple(self) -> tuple[int, int]:
        return (self.x, self.y)


@dataclass(frozen=True)
class ScreenRectangle:
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def center(self) -> ScreenPt:
        return ScreenPt((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)

    @property
    def center_bottom(self) -> ScreenPt:
        return ScreenPt((self.x1 + self.x2) // 2, self.y2)

    @property
    def width(self) -> int:
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        return self.y2 - self.y1

    def as_tuple(self) -> tuple[int, int, int, int]:
        return (self.x1, self.y1, self.x2, self.y2)
