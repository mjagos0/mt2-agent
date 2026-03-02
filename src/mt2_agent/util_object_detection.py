# ./mt2_agent/util_object_detection.py
from .window import Screenshot, ScreenPt, ScreenRectangle

from dataclasses import dataclass
from ultralytics import YOLO
import enum
import logging
import cv2

logger = logging.getLogger(__name__)


class Label(enum.Enum):
    BOSS = "Boss"
    BOULDER = "Boulder"
    ENEMY = "Enemy"


# Map YOLO class IDs to labels — adjust IDs to match your model
YOLO_CLS_TO_LABEL: dict[int, Label] = {
    0: Label.BOSS,
    1: Label.BOULDER,
    2: Label.BOULDER,
    3: Label.ENEMY,
}


@dataclass(frozen=True)
class Detection:
    label: Label
    confidence: float
    rect: ScreenRectangle

    @property
    def center(self) -> ScreenPt:
        return self.rect.center

    @property
    def center_bottom(self) -> ScreenPt:
        return self.rect.center_bottom

    @property
    def width(self) -> int:
        return self.rect.width

    @property
    def height(self) -> int:
        return self.rect.height


@dataclass(frozen=True)
class DetectionResult:
    """Detections pre-indexed by label for O(1) lookups.

    YOLO results are confidence-sorted, so first per label = highest confidence.
    """

    screenshot: Screenshot
    detections: list[Detection]
    _by_label: dict[Label, list[Detection]]

    def __len__(self) -> int:
        return len(self.detections)

    def __iter__(self):
        return iter(self.detections)

    def __bool__(self) -> bool:
        return len(self.detections) > 0

    def by_label(self, label: Label) -> list[Detection]:
        return self._by_label.get(label, [])

    def first(self, label: Label) -> Detection | None:
        """O(1) highest-confidence detection for a given label."""
        dets = self._by_label.get(label)
        return dets[0] if dets else None

    def first_by_priority(self, priority_order: list[Label]) -> Detection | None:
        """Return first detection of the highest-priority label present.

        Args:
            priority_order: labels ordered highest-priority first.
        """
        for label in priority_order:
            det = self.first(label)
            if det is not None:
                return det
        return None

    # In DetectionResult, add this method:

    def annotated(self) -> Screenshot:
        """Return a copy of the screenshot with bounding boxes and centers drawn."""
        img = self.screenshot.data.copy()

        LABEL_COLORS = {
            Label.BOSS: (255, 0, 0),
            Label.BOULDER: (0, 255, 0),
            Label.ENEMY: (0, 0, 255),
        }

        for det in self.detections:
            color = LABEL_COLORS.get(det.label, (255, 255, 255))
            # Offset back to local image coordinates
            ox, oy = self.screenshot.origin_x, self.screenshot.origin_y
            x1 = det.rect.x1 - ox
            y1 = det.rect.y1 - oy
            x2 = det.rect.x2 - ox
            y2 = det.rect.y2 - oy
            cx = det.center.x - ox
            cy = det.center.y - oy

            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            cv2.circle(img, (cx, cy), 4, color, -1)
            cv2.putText(
                img,
                f"{det.label.value} {det.confidence:.2f}",
                (x1, y1 - 6),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
            )

        return Screenshot(
            data=img,
            origin_x=self.screenshot.origin_x,
            origin_y=self.screenshot.origin_y,
        )

    @property
    def bosses(self) -> list[Detection]:
        return self.by_label(Label.BOSS)

    @property
    def boulders(self) -> list[Detection]:
        return self.by_label(Label.BOULDER)

    @property
    def enemies(self) -> list[Detection]:
        return self.by_label(Label.ENEMY)


class ObjectDetector:
    def __init__(
        self,
        model_path: str,
        confidence: float,
        boss_priority: int,
        boulder_priority: int,
        enemy_priority: int,
    ):
        self.model_path = model_path
        self.confidence = confidence
        priorities = {
            Label.BOSS: boss_priority,
            Label.BOULDER: boulder_priority,
            Label.ENEMY: enemy_priority,
        }
        self.priority_order: list[Label] = [
            l for l, _ in sorted(priorities.items(), key=lambda x: x[1], reverse=True)
        ]
        self.yolo = YOLO(self.model_path)

    def detect(self, screenshot: Screenshot) -> DetectionResult:
        results = self.yolo.predict(  # type: ignore[reportUnknownMemberType]
            source=screenshot.data,
            conf=self.confidence,
            verbose=False,
        )

        detections: list[Detection] = []
        by_label: dict[Label, list[Detection]] = {}

        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                label = YOLO_CLS_TO_LABEL.get(int(box.cls[0]))
                if label is None:
                    continue

                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                det = Detection(
                    label=label,
                    confidence=float(box.conf[0]),
                    rect=ScreenRectangle(
                        x1=int(x1) + screenshot.origin_x,
                        y1=int(y1) + screenshot.origin_y,
                        x2=int(x2) + screenshot.origin_x,
                        y2=int(y2) + screenshot.origin_y,
                    ),
                )
                detections.append(det)
                by_label.setdefault(label, []).append(det)

        return DetectionResult(
            screenshot=screenshot,
            detections=detections,
            _by_label=by_label,
        )

    def detect_priority(self, detections: DetectionResult) -> Detection | None:
        return detections.first_by_priority(self.priority_order)
