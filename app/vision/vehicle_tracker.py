# app/vision/vehicle_tracker.py
"""
Feature 1 – Vehicle Detection   (upgrades Basic/Partial → Full)
Feature 2 – Vehicle Tracking    (Missing → Implemented)

YOLOv8 detects vehicles; a centroid-based tracker assigns persistent IDs.
Falls back to a HOG+SVM person detector when ultralytics is not installed.
"""

from __future__ import annotations

import logging
from collections import OrderedDict
from typing import Dict, List, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# COCO class IDs that count as vehicles
_VEHICLE_CLASSES = {2, 3, 5, 7}   # car, motorcycle, bus, truck


# ─────────────────────────────────────────────────────────────────────────────
# Centroid tracker
# ─────────────────────────────────────────────────────────────────────────────

class _CentroidTracker:
    """Assigns stable integer IDs to objects across frames via centroid distance."""

    def __init__(self, max_disappeared: int = 40) -> None:
        self.next_id = 0
        self.objects: OrderedDict[int, Tuple[int, int]]         = OrderedDict()
        self.bboxes:  OrderedDict[int, Tuple[int, int, int, int]] = OrderedDict()
        self.disappeared: OrderedDict[int, int]                 = OrderedDict()
        self.max_disappeared = max_disappeared

    def register(self, centroid: Tuple[int, int], bbox: Tuple[int, int, int, int]) -> None:
        self.objects[self.next_id]      = centroid
        self.bboxes[self.next_id]       = bbox
        self.disappeared[self.next_id]  = 0
        self.next_id += 1

    def deregister(self, obj_id: int) -> None:
        for d in (self.objects, self.bboxes, self.disappeared):
            d.pop(obj_id, None)

    def update(
        self, detections: List[Tuple[int, int, int, int]]
    ) -> Dict[int, dict]:
        """
        detections: list of (x1, y1, x2, y2)
        Returns {id: {'centroid': (cx, cy), 'bbox': (x1,y1,x2,y2)}}
        """
        if not detections:
            for oid in list(self.disappeared):
                self.disappeared[oid] += 1
                if self.disappeared[oid] > self.max_disappeared:
                    self.deregister(oid)
            return self._export()

        new_centroids = [((x1 + x2) // 2, (y1 + y2) // 2) for x1, y1, x2, y2 in detections]

        if not self.objects:
            for c, b in zip(new_centroids, detections):
                self.register(c, b)
            return self._export()

        oids   = list(self.objects.keys())
        ocents = np.array(list(self.objects.values()), dtype=float)
        ncents = np.array(new_centroids, dtype=float)

        D = np.linalg.norm(ocents[:, None] - ncents[None, :], axis=2)
        rows = D.min(axis=1).argsort()
        cols = D.argmin(axis=1)[rows]

        used_rows, used_cols = set(), set()
        for r, c in zip(rows, cols):
            if r in used_rows or c in used_cols:
                continue
            oid = oids[r]
            self.objects[oid]     = new_centroids[c]
            self.bboxes[oid]      = detections[c]
            self.disappeared[oid] = 0
            used_rows.add(r); used_cols.add(c)

        for r in set(range(len(oids))) - used_rows:
            oid = oids[r]
            self.disappeared[oid] += 1
            if self.disappeared[oid] > self.max_disappeared:
                self.deregister(oid)

        for c in set(range(len(detections))) - used_cols:
            self.register(new_centroids[c], detections[c])

        return self._export()

    def _export(self) -> Dict[int, dict]:
        return {
            oid: {"centroid": self.objects[oid], "bbox": self.bboxes[oid]}
            for oid in self.objects
        }


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

class VehicleTracker:
    """
    Detects vehicles with YOLOv8 (or HOG fallback) and tracks them
    across frames with stable integer IDs.
    """

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        conf: float = 0.45,
        max_disappeared: int = 40,
    ) -> None:
        self._conf    = conf
        self._tracker = _CentroidTracker(max_disappeared)
        self._model   = None
        self._hog     = None
        self._load_model(model_path)

    # ------------------------------------------------------------------
    def _load_model(self, path: str) -> None:
        try:
            from ultralytics import YOLO          # type: ignore
            self._model = YOLO(path)
            logger.info("VehicleTracker: YOLOv8 loaded (%s).", path)
        except Exception as exc:
            logger.warning("YOLOv8 unavailable (%s). Using HOG fallback.", exc)
            self._hog = cv2.HOGDescriptor()
            self._hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    # ------------------------------------------------------------------
    def update(self, frame: np.ndarray) -> Dict[int, dict]:
        """
        Run detection + tracking on *frame*.
        Returns {track_id: {'centroid': (cx,cy), 'bbox': (x1,y1,x2,y2)}}.
        Also draws bounding boxes and IDs on *frame* in-place.
        """
        boxes = self._detect(frame)
        tracked = self._tracker.update(boxes)

        for tid, info in tracked.items():
            x1, y1, x2, y2 = info["bbox"]
            cx, cy = info["centroid"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 200, 255), 2)
            cv2.putText(frame, f"V{tid}", (x1, y1 - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1)
            cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)

        return tracked

    # ------------------------------------------------------------------
    def _detect(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        if self._model is not None:
            results = self._model(frame, conf=self._conf, verbose=False)
            boxes = []
            for r in results:
                for box in r.boxes:
                    if int(box.cls[0]) in _VEHICLE_CLASSES:
                        boxes.append(tuple(map(int, box.xyxy[0])))
            return boxes

        # HOG fallback (detects people; approximate for vehicles)
        gray   = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects, _ = self._hog.detectMultiScale(gray, winStride=(8, 8), padding=(4, 4))
        return [(x, y, x + w, y + h) for x, y, w, h in rects]
