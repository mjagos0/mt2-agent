from dataclasses import dataclass

NAMED_ANCHORS = {
    "top-left":      (0.0, 0.0),
    "top-right":     (1.0, 0.0),
    "bottom-left":   (0.0, 1.0),
    "bottom-right":  (1.0, 1.0),
    "center":        (0.5, 0.5),
    "bottom-center": (0.5, 1.0),
    "top-center":    (0.5, 0.0)
}

@dataclass
class GamePt:
    anchor: tuple[float, float]
    offset: tuple[float, float]

    @property
    def widthAnchor(self) -> float:
        return self.anchor[0]
    
    @property
    def heightAnchor(self) -> float:
        return self.anchor[1]
    
    @property
    def widthOffset(self) -> float:
        return self.offset[0]
    
    @property
    def heightOffset(self) -> float:
        return self.offset[1]
    
@dataclass
class GameRec(GamePt):
    dimensions: tuple[int, int]

    @property
    def width(self) -> float:
        return self.dimensions[0]
    
    @property
    def height(self) -> float:
        return self.dimensions[1]
