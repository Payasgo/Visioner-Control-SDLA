# app/vision/road_scene.py
"""
Feature 15 – Traffic Light Detection   (Missing → Implemented)
Feature 16 – Traffic Sign Recognition  (Missing → Implemented)
Feature 17 – Collision Warning         (Missing → Implemented)
Feature 18 – Pedestrian Detection      (Missing → Implemented)
Feature 19 – Obstacle Detection        (Missing → Implemented)
Feature 20 – Blind Spot Detection      (Missing → Implemented)
Feature 21 – Parking Assistance        (Missing → Implemented)
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def _yolo(path: str):
    try:
        from ultralytics import YOLO          # type: ignore
        return YOLO(path)
    except Exception as exc:
        logger.warning("YOLO not loaded for road_scene (%s).", exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 1. Traffic Light Detector
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TrafficLightResult:
    state: str          # "RED" | "AMBER" | "GREEN" | "UNKNOWN"
    red_light_violation: bool


class TrafficLightDetector:
    """
    Detects traffic signal state via HSV colour segmentation (upper frame).
    Flags a red-light violation when any tracked vehicle crosses the stop line
    while the signal is RED.
    """

    STOP_LINE_Y = 0.70     # fraction of frame height

    def __init__(self, model_path: Optional[str] = None) -> None:
        self._model   = _yolo(model_path) if model_path else None
        self._state   = "UNKNOWN"
        self._alerted: set = set()

    @property
    def state(self) -> str:
        return self._state

    def process(
        self, frame: np.ndarray, tracked_vehicles: Dict[int, dict]
    ) -> TrafficLightResult:
        h, w = frame.shape[:2]
        stop_y = int(h * self.STOP_LINE_Y)

        self._state = self._detect_state(frame)
        color_map = {"RED": (0,0,255), "AMBER": (0,165,255),
                     "GREEN": (0,255,0), "UNKNOWN": (128,128,128)}
        col = color_map.get(self._state, (128,128,128))
        cv2.line(frame, (0, stop_y), (w, stop_y), col, 2)
        cv2.putText(frame, f"SIGNAL: {self._state}", (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, col, 2)

        violation = False
        if self._state == "RED":
            for tid, info in tracked_vehicles.items():
                _, _, _, y2 = info["bbox"]
                if y2 > stop_y and tid not in self._alerted:
                    self._alerted.add(tid)
                    violation = True
                    cv2.putText(frame, "RED LIGHT VIOLATION!", (10, 115),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            self._alerted.clear()

        return TrafficLightResult(self._state, violation)

    def _detect_state(self, frame: np.ndarray) -> str:
        h, w = frame.shape[:2]
        roi  = frame[: h // 3, w // 4: 3 * w // 4]
        hsv  = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        r1   = cv2.inRange(hsv, (0,  120, 70), (10, 255, 255))
        r2   = cv2.inRange(hsv, (170, 120, 70), (180,255,255))
        red  = cv2.bitwise_or(r1, r2)
        amb  = cv2.inRange(hsv, (10, 120, 70), (30, 255, 255))
        grn  = cv2.inRange(hsv, (40,  60, 70), (90, 255, 255))
        counts = {"RED": cv2.countNonZero(red),
                  "AMBER": cv2.countNonZero(amb),
                  "GREEN": cv2.countNonZero(grn)}
        best = max(counts, key=counts.get)
        return best if counts[best] > 200 else "UNKNOWN"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Traffic Sign Recognizer
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SignResult:
    label: str
    bbox: Tuple[int, int, int, int]     # x1,y1,x2,y2 in frame coords


class TrafficSignRecognizer:
    """
    Recognises road signs via colour+shape heuristic, or a custom YOLO model.
    Categories (heuristic): STOP, WARNING, INFO.
    """

    def __init__(self, model_path: Optional[str] = None) -> None:
        self._model = _yolo(model_path) if model_path else None

    def process(
        self, frame: np.ndarray
    ) -> List[SignResult]:
        signs = self._detect(frame)
        for s in signs:
            x1, y1, x2, y2 = s.bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 200, 0), 2)
            cv2.putText(frame, s.label, (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 2)
        return signs

    def _detect(self, frame: np.ndarray) -> List[SignResult]:
        if self._model:
            out = []
            for r in self._model(frame, verbose=False):
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    label = self._model.names.get(int(box.cls[0]), "SIGN").upper()
                    out.append(SignResult(label, (x1, y1, x2, y2)))
            return out
        return self._heuristic(frame)

    @staticmethod
    def _heuristic(frame: np.ndarray) -> List[SignResult]:
        hsv  = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        out  = []
        specs = [
            ("STOP",    cv2.bitwise_or(
                cv2.inRange(hsv, (0, 140, 70), (10,  255, 255)),
                cv2.inRange(hsv, (170,140, 70), (180, 255, 255)))),
            ("WARNING", cv2.inRange(hsv, (20, 100, 100), (35, 255, 255))),
            ("INFO",    cv2.inRange(hsv, (100, 100, 50), (130, 255, 255))),
        ]
        for label, mask in specs:
            k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            m = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)
            cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            h, w    = frame.shape[:2]
            for c in cnts:
                area = cv2.contourArea(c)
                if area < 400 or area > 0.1 * h * w:
                    continue
                x, y, bw, bh = cv2.boundingRect(c)
                out.append(SignResult(label, (x, y, x + bw, y + bh)))
        return out


# ─────────────────────────────────────────────────────────────────────────────
# 3. Collision Warning (TTC)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CollisionAlert:
    track_id: int
    ttc_seconds: float


class CollisionWarning:
    """
    Estimates Time-to-Collision via bounding-box area growth.
    TTC ≈ area / (d_area / dt)
    """

    WARN_S  = 3.0
    ALERT_S = 1.5

    def __init__(self) -> None:
        import time as _time
        self._time      = _time
        self._prev_area: Dict[int, float] = {}
        self._prev_ts:   Dict[int, float] = {}
        self._alerted: set = set()

    def process(
        self, frame: np.ndarray, tracked_vehicles: Dict[int, dict]
    ) -> List[CollisionAlert]:
        alerts = []
        now    = self._time.time()
        for tid, info in tracked_vehicles.items():
            x1, y1, x2, y2 = info["bbox"]
            area = float((x2 - x1) * (y2 - y1))
            if tid in self._prev_area and tid in self._prev_ts:
                dt = now - self._prev_ts[tid]
                da = area - self._prev_area[tid]
                if dt > 0 and da > 0:
                    ttc = min(area / (da / dt), 999.9)
                    col = (0,255,0) if ttc > self.WARN_S else \
                          (0,165,255) if ttc > self.ALERT_S else (0,0,255)
                    cv2.putText(frame, f"TTC:{ttc:.1f}s",
                                (info["bbox"][0], info["bbox"][1] - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, col, 1)
                    if ttc < self.ALERT_S and tid not in self._alerted:
                        self._alerted.add(tid)
                        alerts.append(CollisionAlert(tid, ttc))
                    elif ttc >= self.WARN_S:
                        self._alerted.discard(tid)
            self._prev_area[tid] = area
            self._prev_ts[tid]   = now
        return alerts


# ─────────────────────────────────────────────────────────────────────────────
# 4. Pedestrian Detector
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PedAlert:
    track_id: int
    distance_px: float


class PedestrianDetector:
    """
    Detects pedestrians (COCO class 0 / HOG) and alerts when a vehicle
    is dangerously close.
    """

    PERSON_CLS  = 0
    PROX_THRESH = 80.0     # pixels

    def __init__(self, model_path: str = "yolov8n.pt") -> None:
        self._model = _yolo(model_path)
        self._hog   = cv2.HOGDescriptor()
        self._hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        self._alerted: set = set()

    def process(
        self, frame: np.ndarray, tracked_vehicles: Dict[int, dict]
    ) -> List[PedAlert]:
        peds   = self._detect(frame)
        alerts = []
        for pb in peds:
            cv2.rectangle(frame, pb[:2], pb[2:], (255, 0, 255), 2)
            cv2.putText(frame, "PEDESTRIAN", (pb[0], pb[1] - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 255), 1)
        for tid, info in tracked_vehicles.items():
            vb = info["bbox"]
            for pb in peds:
                d = self._edge_dist(vb, pb)
                if d < self.PROX_THRESH:
                    cv2.putText(frame, "PED ALERT!", (vb[0], vb[1] - 70),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
                    key = (tid, pb[0], pb[1])
                    if key not in self._alerted:
                        self._alerted.add(key)
                        alerts.append(PedAlert(tid, d))
        return alerts

    def _detect(self, frame) -> List[Tuple]:
        if self._model:
            out = []
            for r in self._model(frame, conf=0.40, verbose=False):
                for box in r.boxes:
                    if int(box.cls[0]) == self.PERSON_CLS:
                        out.append(tuple(map(int, box.xyxy[0])))
            return out
        gray   = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects, _ = self._hog.detectMultiScale(
            gray, winStride=(8,8), padding=(4,4), scale=1.05)
        return [(x, y, x+w, y+h) for x,y,w,h in rects]

    @staticmethod
    def _edge_dist(a, b) -> float:
        dx = max(0, max(a[0], b[0]) - min(a[2], b[2]))
        dy = max(0, max(a[1], b[1]) - min(a[3], b[3]))
        return float(np.hypot(dx, dy))


# ─────────────────────────────────────────────────────────────────────────────
# 5. Obstacle Detector
# ─────────────────────────────────────────────────────────────────────────────

class ObstacleDetector:
    """
    Detects stationary obstacles via MOG2 background subtraction
    in the lower road region.
    """

    MIN_AREA     = 1500
    ALERT_DIST   = 120

    def __init__(self) -> None:
        self._bg     = cv2.createBackgroundSubtractorMOG2(
            history=300, varThreshold=50, detectShadows=False)
        self._alerted: set = set()

    def process(
        self, frame: np.ndarray, tracked_vehicles: Dict[int, dict]
    ) -> int:
        """Returns count of obstacles detected."""
        h, w = frame.shape[:2]
        road = frame[h // 2:, :]
        fg   = self._bg.apply(road)
        k    = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        fg   = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, k)
        fg   = cv2.morphologyEx(fg, cv2.MORPH_OPEN,  k)
        n, _, stats, _ = cv2.connectedComponentsWithStats(fg)
        count = 0
        for i in range(1, n):
            area = stats[i, cv2.CC_STAT_AREA]
            if area < self.MIN_AREA:
                continue
            ox  = stats[i, cv2.CC_STAT_LEFT]
            oy  = stats[i, cv2.CC_STAT_TOP] + h // 2
            ow_ = stats[i, cv2.CC_STAT_WIDTH]
            oh_ = stats[i, cv2.CC_STAT_HEIGHT]
            cv2.rectangle(frame, (ox, oy), (ox+ow_, oy+oh_), (0, 128, 255), 2)
            cv2.putText(frame, "OBSTACLE", (ox, oy-6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 128, 255), 1)
            count += 1
            for tid, info in tracked_vehicles.items():
                cx, cy = info["centroid"]
                if ox < cx < ox + ow_ and cy < oy:
                    if oy - cy < self.ALERT_DIST:
                        key = (tid, ox, oy)
                        if key not in self._alerted:
                            self._alerted.add(key)
                            logger.warning("[OBSTACLE] tid=%s close obstacle", tid)
        return count


# ─────────────────────────────────────────────────────────────────────────────
# 6. Blind Spot Detector
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class BlindSpotAlert:
    side: str      # "LEFT" | "RIGHT"
    intruder_id: int


class BlindSpotDetector:
    """
    Flags vehicles entering the left/right blind-spot zones of the ego vehicle.
    """

    ZONE_W = 120       # pixels

    def __init__(self) -> None:
        self._alerted: set = set()

    def process(
        self, frame: np.ndarray, tracked_vehicles: Dict[int, dict]
    ) -> List[BlindSpotAlert]:
        h, w = frame.shape[:2]
        ego  = self._ego(tracked_vehicles, h, w)
        if ego is None:
            return []
        ego_id, info = ego
        ex1, ey1, ex2, ey2 = info["bbox"]
        mid_y   = (ey1 + ey2) // 2
        zone_h  = (ey2 - ey1)
        alerts  = []
        for side, zone in [
            ("LEFT",  (max(0, ex1 - self.ZONE_W), mid_y - zone_h//2,
                       ex1, mid_y + zone_h//2)),
            ("RIGHT", (ex2, mid_y - zone_h//2,
                       min(w, ex2 + self.ZONE_W), mid_y + zone_h//2)),
        ]:
            cv2.rectangle(frame, zone[:2], zone[2:], (200, 200, 0), 1)
            for tid, vinfo in tracked_vehicles.items():
                if tid == ego_id:
                    continue
                cx, cy = vinfo["centroid"]
                if zone[0] < cx < zone[2] and zone[1] < cy < zone[3]:
                    cv2.rectangle(frame, zone[:2], zone[2:], (0, 0, 255), 3)
                    cv2.putText(frame, f"BLIND SPOT {side}!",
                                (zone[0], zone[1] - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                    key = (ego_id, tid, side)
                    if key not in self._alerted:
                        self._alerted.add(key)
                        alerts.append(BlindSpotAlert(side, tid))
        return alerts

    @staticmethod
    def _ego(tracked, h, w):
        best_id, best_area = None, 0
        for tid, info in tracked.items():
            x1, y1, x2, y2 = info["bbox"]
            cx, cy = info["centroid"]
            if cy < h * 0.5 or cx < w * 0.2 or cx > w * 0.8:
                continue
            a = (x2 - x1) * (y2 - y1)
            if a > best_area:
                best_area = a; best_id = tid
        return (best_id, tracked[best_id]) if best_id is not None else None


# ─────────────────────────────────────────────────────────────────────────────
# 7. Parking Assistant
# ─────────────────────────────────────────────────────────────────────────────

class ParkingAssistant:
    """
    3×3 proximity grid overlay using KNN background subtraction on the
    lower portion of the frame (proxy for a rear-view feed).
    """

    def __init__(self) -> None:
        self._bg = cv2.createBackgroundSubtractorKNN(
            history=200, dist2Threshold=400, detectShadows=False)
        self._warned = False

    def process(self, frame: np.ndarray) -> str:
        """Returns status string: 'STOP', 'CAUTION', or 'CLEAR'."""
        h, w   = frame.shape[:2]
        rear   = frame[int(h * 0.65):, :]
        fg     = self._bg.apply(rear)
        k      = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        fg     = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, k)
        rh, rw = rear.shape[:2]
        cH, cW = rh // 3, rw // 3
        oy     = int(h * 0.65)
        status = "CLEAR"

        for r in range(3):
            for c in range(3):
                y0, y1_ = r * cH, (r + 1) * cH
                x0, x1_ = c * cW, (c + 1) * cW
                d = cv2.countNonZero(fg[y0:y1_, x0:x1_]) / max((y1_-y0)*(x1_-x0), 1)
                if d > 0.35:
                    col, txt = (0, 0, 255), "!!!"
                    if r == 0:
                        status = "STOP"
                elif d > 0.15:
                    col, txt = (0, 165, 255), " ! "
                    if status == "CLEAR":
                        status = "CAUTION"
                else:
                    col, txt = (0, 200, 0), "   "
                cv2.rectangle(frame, (x0, y0+oy), (x1_, y1_+oy), col, 1)
                cv2.putText(frame, txt, (x0 + cW//3, y0+oy + cH//2),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 1)

        cv2.putText(frame, f"PARKING ASSIST: {status}", (10, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 200), 1)
        return status
