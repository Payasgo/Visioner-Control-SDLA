# app/vision/anpr.py
"""
Feature 6 – License Plate Recognition / ANPR  (Missing → Implemented)
Feature 7 – OCR                                (Missing → Implemented)

Pipeline:
  1. Candidate regions found via contour analysis on an edge map.
  2. Best candidate classified as a plate by aspect-ratio heuristic.
  3. Text extracted with pytesseract (falls back to empty string if absent).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Regex for common plate formats (alphanumeric, 4-10 chars)
_PLATE_RE = re.compile(r"[A-Z0-9]{4,10}")


@dataclass
class PlateResult:
    text: str
    bbox: Tuple[int, int, int, int]   # x, y, w, h  (full-frame coords)
    confidence: float                  # 0.0 – 1.0


class ANPRProcessor:
    """
    Detects and reads license plates from a BGR frame (or a vehicle ROI).

    Parameters
    ----------
    min_plate_w, min_plate_h:
        Minimum plate dimensions in pixels.
    aspect_lo, aspect_hi:
        Accepted width/height ratio range for plate candidates.
    """

    def __init__(
        self,
        min_plate_w: int = 60,
        min_plate_h: int = 15,
        aspect_lo: float = 2.0,
        aspect_hi: float = 6.5,
    ) -> None:
        self._min_w = min_plate_w
        self._min_h = min_plate_h
        self._asp_lo = aspect_lo
        self._asp_hi = aspect_hi
        self._has_tesseract = self._check_tesseract()

    # ------------------------------------------------------------------
    @staticmethod
    def _check_tesseract() -> bool:
        try:
            import pytesseract                       # type: ignore
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            logger.warning("pytesseract / Tesseract not found. OCR disabled.")
            return False

    # ------------------------------------------------------------------
    def process_frame(
        self, frame: np.ndarray, bbox: Optional[Tuple[int, int, int, int]] = None
    ) -> Optional[PlateResult]:
        """
        Run ANPR on *frame* (optionally restricted to *bbox* = (x,y,w,h)).
        Returns the best PlateResult or None.
        """
        if bbox:
            x, y, w, h = bbox
            roi = frame[y: y + h, x: x + w]
            offset = (x, y)
        else:
            roi    = frame
            offset = (0, 0)

        candidate = self._find_plate_region(roi)
        if candidate is None:
            return None

        cx, cy, cw, ch = candidate
        plate_img = roi[cy: cy + ch, cx: cx + cw]
        text  = self._ocr(plate_img)
        conf  = 0.9 if _PLATE_RE.search(text) else 0.4

        # Draw on frame
        fx, fy = offset[0] + cx, offset[1] + cy
        cv2.rectangle(frame, (fx, fy), (fx + cw, fy + ch), (0, 255, 255), 2)
        cv2.putText(frame, text or "PLATE?", (fx, fy - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)

        return PlateResult(text=text, bbox=(fx, fy, cw, ch), confidence=conf)

    # ------------------------------------------------------------------
    def _find_plate_region(
        self, roi: np.ndarray
    ) -> Optional[Tuple[int, int, int, int]]:
        gray   = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blur   = cv2.bilateralFilter(gray, 11, 17, 17)
        edges  = cv2.Canny(blur, 30, 200)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edges  = cv2.dilate(edges, kernel, iterations=1)

        cnts, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cnts    = sorted(cnts, key=cv2.contourArea, reverse=True)[:20]

        for c in cnts:
            peri  = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.018 * peri, True)
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                if w < self._min_w or h < self._min_h:
                    continue
                aspect = w / max(h, 1)
                if self._asp_lo <= aspect <= self._asp_hi:
                    return x, y, w, h

        # Fallback: largest rect-like contour above minimum size
        for c in cnts:
            x, y, w, h = cv2.boundingRect(c)
            if w >= self._min_w and h >= self._min_h:
                aspect = w / max(h, 1)
                if self._asp_lo <= aspect <= self._asp_hi:
                    return x, y, w, h

        return None

    # ------------------------------------------------------------------
    def _ocr(self, plate_img: np.ndarray) -> str:
        if not self._has_tesseract or plate_img.size == 0:
            return ""
        try:
            import pytesseract                       # type: ignore
            gray  = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
            gray  = cv2.resize(gray, None, fx=2, fy=2,
                               interpolation=cv2.INTER_CUBIC)
            _, th = cv2.threshold(gray, 0, 255,
                                   cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            text = pytesseract.image_to_string(
                th,
                config="--psm 8 -c tessedit_char_whitelist="
                       "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
            ).strip()
            return text
        except Exception as exc:
            logger.debug("OCR error: %s", exc)
            return ""
