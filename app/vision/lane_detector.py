# app/vision/lane_detector.py
"""
Feature 4 – Lane Detection       (Basic → Full)
Feature 5 – Lane Departure Warning (Partial → Full)

Hough-line pipeline with EMA smoothing.  Emits LaneDepartureEvent
when a vehicle centroid drifts beyond the configured threshold.
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class LaneDepartureEvent:
    track_id: int
    deviation_px: float
    direction: str      # "LEFT" | "RIGHT"


class LaneDetector:
    """
    Detects lane lines and issues departure warnings.

    Parameters
    ----------
    departure_threshold_px:
        Lateral pixel deviation from the established baseline that
        triggers a departure warning.
    history_frames:
        Number of frames used to establish the baseline centroid.
    alpha:
        EMA coefficient for smoothing detected lane lines (0 < alpha ≤ 1).
    """

    def __init__(
        self,
        departure_threshold_px: float = 60.0,
        history_frames: int = 15,
        alpha: float = 0.15,
    ) -> None:
        self._threshold  = departure_threshold_px
        self._hist_len   = history_frames
        self._alpha      = alpha

        self._left_line: Optional[Tuple]  = None
        self._right_line: Optional[Tuple] = None

        self._cx_history: Dict[int, deque] = defaultdict(
            lambda: deque(maxlen=history_frames)
        )
        self._baseline_cx: Dict[int, float] = {}
        self._alerted: set = set()

    # ------------------------------------------------------------------
    def process(
        self,
        frame: np.ndarray,
        tracked_vehicles: Dict[int, dict],
    ) -> Tuple[np.ndarray, list]:
        """
        Detect lanes, overlay them on *frame*, and check each tracked
        vehicle for departure.

        Returns
        -------
        frame     : annotated frame
        departures: list of LaneDepartureEvent
        """
        h, w = frame.shape[:2]
        left, right = self._detect_lanes(frame, h, w)
        self._left_line  = self._ema(self._left_line,  left)
        self._right_line = self._ema(self._right_line, right)
        frame = self._draw_lanes(frame, h, w)

        departures: list[LaneDepartureEvent] = []
        for tid, info in tracked_vehicles.items():
            cx, _ = info["centroid"]
            self._cx_history[tid].append(cx)

            if (len(self._cx_history[tid]) >= self._hist_len
                    and tid not in self._baseline_cx):
                self._baseline_cx[tid] = float(np.mean(self._cx_history[tid]))

            if tid in self._baseline_cx:
                dev = cx - self._baseline_cx[tid]
                if abs(dev) > self._threshold:
                    direction = "RIGHT" if dev > 0 else "LEFT"
                    if tid not in self._alerted:
                        self._alerted.add(tid)
                        departures.append(LaneDepartureEvent(tid, abs(dev), direction))
                    x1, y1, x2, y2 = info["bbox"]
                    cv2.putText(frame, f"LANE DEPART {direction}",
                                (x1, y1 - 22),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                else:
                    self._alerted.discard(tid)
                    self._baseline_cx[tid] = (
                        0.95 * self._baseline_cx[tid] + 0.05 * cx
                    )

        return frame, departures

    # ------------------------------------------------------------------
    def _detect_lanes(self, frame, h, w):
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur  = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)
        roi   = self._roi(edges, h, w)
        lines = cv2.HoughLinesP(roi, 1, np.pi / 180,
                                  threshold=50, minLineLength=80, maxLineGap=120)
        lefts, rights = [], []
        if lines is not None:
            for x1, y1, x2, y2 in lines[:, 0]:
                if x2 == x1:
                    continue
                slope = (y2 - y1) / (x2 - x1)
                if abs(slope) < 0.4:
                    continue
                (lefts if slope < 0 else rights).append((x1, y1, x2, y2))
        left  = self._avg_line(lefts,  h) if lefts  else None
        right = self._avg_line(rights, h) if rights else None
        return left, right

    @staticmethod
    def _roi(img, h, w):
        mask = np.zeros_like(img)
        poly = np.array([[
            (int(w * 0.05), h),
            (int(w * 0.45), int(h * 0.55)),
            (int(w * 0.55), int(h * 0.55)),
            (int(w * 0.95), h),
        ]], dtype=np.int32)
        cv2.fillPoly(mask, poly, 255)
        return cv2.bitwise_and(img, mask)

    @staticmethod
    def _avg_line(segs, h):
        xs, ys = [], []
        for x1, y1, x2, y2 in segs:
            xs += [x1, x2]; ys += [y1, y2]
        poly = np.polyfit(ys, xs, 1)
        y1_ = h; y2_ = int(h * 0.55)
        return int(np.polyval(poly, y1_)), y1_, int(np.polyval(poly, y2_)), y2_

    def _ema(self, prev, curr):
        if curr is None:
            return prev
        if prev is None:
            return curr
        return tuple(int(self._alpha * c + (1 - self._alpha) * p)
                     for p, c in zip(prev, curr))

    def _draw_lanes(self, frame, h, w):
        overlay = frame.copy()
        if self._left_line and self._right_line:
            lx1, ly1, lx2, ly2 = self._left_line
            rx1, ry1, rx2, ry2 = self._right_line
            pts = np.array(
                [[lx1, ly1], [lx2, ly2], [rx2, ry2], [rx1, ry1]], np.int32)
            cv2.fillPoly(overlay, [pts], (0, 200, 0))
            cv2.addWeighted(overlay, 0.25, frame, 0.75, 0, frame)
        for line, colour in [
            (self._left_line,  (0, 255, 100)),
            (self._right_line, (0, 255, 100)),
        ]:
            if line:
                cv2.line(frame, (line[0], line[1]), (line[2], line[3]), colour, 3)
        cv2.putText(frame, "LANE DETECTION ACTIVE", (10, 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 100), 1)
        return frame
