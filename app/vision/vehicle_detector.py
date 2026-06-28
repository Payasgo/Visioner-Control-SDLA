# app/vision/vehicle_detector.py
"""
Vehicle Detection & Tracking
=============================
Feature #1  – Vehicle Detection    (upgrades Basic/Partial → Full YOLO)
Feature #2  – Vehicle Tracking     (centroid-based tracker with unique IDs)

Architecture
------------
VehicleDetector   – runs YOLOv8 (or HOG fallback) and returns bounding boxes
CentroidTracker   – assigns stable IDs to detections across frames
VehicleTracker    – composes both into a single update() call used by main pipeline
"""

import cv2
import numpy as np
from collections import OrderedDict
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# YOLO helper
# ─────────────────────────────────────────────────────────────────────────────

def _load_yolo(model_path: str = "yolov8n.pt"):
    try:
        from ultralytics import YOLO  # type: ignore
        model = YOLO(model_path)
        print(f"[VehicleDetector] YOLOv8 loaded: {model_path}")
        return model
    except Exception as exc:
        print(f"[VehicleDetector] YOLO unavailable ({exc}). Using HOG fallback.")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 1. Vehicle Detector
# ─────────────────────────────────────────────────────────────────────────────

# COCO class IDs that count as vehicles
_VEHICLE_CLASSES = {2, 3, 5, 7}  # car, motorcycle, bus, truck


class VehicleDetector:
    """
    Detects vehicles in a single frame.

    Returns a list of (x1, y1, x2, y2, class_id, confidence) tuples.
    Falls back to a HOG people-detector when YOLO is unavailable
    (useful for CI / headless environments without a GPU).
    """

    def __init__(self, model_path: str = "yolov8n.pt",
                 conf: float = 0.40, iou: float = 0.45) -> None:
        self._model = _load_yolo(model_path)
        self._conf  = conf
        self._iou   = iou

        # HOG fallback (detects people, used here as a demo substitute)
        self._hog = cv2.HOGDescriptor()
        self._hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    # ------------------------------------------------------------------
    def detect(self, frame: np.ndarray) -> list[tuple]:
        """Return list of (x1, y1, x2, y2, class_id, conf)."""
        if self._model is not None:
            return self._yolo_detect(frame)
        return self._hog_detect(frame)

    # ------------------------------------------------------------------
    def _yolo_detect(self, frame: np.ndarray) -> list[tuple]:
        results = self._model(frame, conf=self._conf,
                               iou=self._iou, verbose=False)
        boxes = []
        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                if cls not in _VEHICLE_CLASSES:
                    continue
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                boxes.append((x1, y1, x2, y2, cls, conf))
        return boxes

    def _hog_detect(self, frame: np.ndarray) -> list[tuple]:
        gray   = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects, _ = self._hog.detectMultiScale(
            gray, winStride=(8, 8), padding=(4, 4), scale=1.05)
        return [(x, y, x + w, y + h, -1, 1.0) for (x, y, w, h) in rects]


# ─────────────────────────────────────────────────────────────────────────────
# 2. Centroid Tracker
# ─────────────────────────────────────────────────────────────────────────────

class CentroidTracker:
    """
    Assigns a stable integer ID to each vehicle across frames using the
    nearest-centroid heuristic.

    Returns a dict: {id: {"centroid": (cx, cy), "bbox": (x1,y1,x2,y2),
                           "class_id": int, "age": int}}
    """

    def __init__(self, max_disappeared: int = 40) -> None:
        self.next_id      = 0
        self._objects     = OrderedDict()   # id → centroid
        self._bboxes      = OrderedDict()   # id → bbox
        self._classes     = OrderedDict()   # id → class_id
        self._disappeared = OrderedDict()   # id → frames since last seen
        self._age         = OrderedDict()   # id → total frames seen
        self.max_disappeared = max_disappeared

    # ------------------------------------------------------------------
    def update(self, detections: list[tuple]) -> dict:
        """
        detections: list of (x1, y1, x2, y2, class_id, conf)
        Returns:    {id: {"centroid", "bbox", "class_id", "age"}}
        """
        if not detections:
            for oid in list(self._disappeared):
                self._disappeared[oid] += 1
                if self._disappeared[oid] > self.max_disappeared:
                    self._deregister(oid)
            return self._as_dict()

        input_centroids, input_bboxes, input_classes = [], [], []
        for (x1, y1, x2, y2, cls, _conf) in detections:
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            input_centroids.append((cx, cy))
            input_bboxes.append((x1, y1, x2, y2))
            input_classes.append(cls)

        if not self._objects:
            for i in range(len(input_centroids)):
                self._register(input_centroids[i], input_bboxes[i], input_classes[i])
        else:
            obj_ids   = list(self._objects.keys())
            obj_cents = list(self._objects.values())

            D = np.linalg.norm(
                np.array(obj_cents)[:, np.newaxis] - np.array(input_centroids),
                axis=2)
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            used_rows, used_cols = set(), set()
            for row, col in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue
                oid = obj_ids[row]
                self._objects[oid]     = input_centroids[col]
                self._bboxes[oid]      = input_bboxes[col]
                self._classes[oid]     = input_classes[col]
                self._disappeared[oid] = 0
                self._age[oid]        += 1
                used_rows.add(row)
                used_cols.add(col)

            for row in set(range(D.shape[0])) - used_rows:
                oid = obj_ids[row]
                self._disappeared[oid] += 1
                if self._disappeared[oid] > self.max_disappeared:
                    self._deregister(oid)

            for col in set(range(D.shape[1])) - used_cols:
                self._register(input_centroids[col],
                                input_bboxes[col], input_classes[col])

        return self._as_dict()

    # ------------------------------------------------------------------
    def _register(self, centroid, bbox, cls):
        self._objects[self.next_id]     = centroid
        self._bboxes[self.next_id]      = bbox
        self._classes[self.next_id]     = cls
        self._disappeared[self.next_id] = 0
        self._age[self.next_id]         = 1
        self.next_id += 1

    def _deregister(self, oid):
        for store in (self._objects, self._bboxes,
                      self._classes, self._disappeared, self._age):
            del store[oid]

    def _as_dict(self) -> dict:
        return {
            oid: {
                "centroid": self._objects[oid],
                "bbox":     self._bboxes[oid],
                "class_id": self._classes[oid],
                "age":      self._age[oid],
            }
            for oid in self._objects
        }


# ─────────────────────────────────────────────────────────────────────────────
# 3. Combined VehicleTracker (convenience facade)
# ─────────────────────────────────────────────────────────────────────────────

class VehicleTracker:
    """Detect + track in one call. Draws bounding boxes on the frame."""

    def __init__(self, model_path: str = "yolov8n.pt") -> None:
        self._detector = VehicleDetector(model_path)
        self._tracker  = CentroidTracker()

    def update(self, frame: np.ndarray) -> dict:
        """Detect vehicles, update tracker, annotate frame. Returns tracked dict."""
        detections = self._detector.detect(frame)
        tracked    = self._tracker.update(detections)

        for oid, info in tracked.items():
            x1, y1, x2, y2 = info["bbox"]
            cx, cy = info["centroid"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 200, 255), 2)
            cv2.putText(frame, f"V{oid}", (x1, y1 - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1)
            cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)

        return tracked
