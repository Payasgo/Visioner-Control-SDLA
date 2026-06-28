# app/enforcement/evidence.py
"""
Feature 25 – Evidence Capture   (Missing → Implemented)
Feature 26 – Violation Logging  (Missing → Implemented)

EvidenceCapture  – saves timestamped JPEG snapshots to disk
ViolationLogger  – appends structured records to a CSV + optional JSON log
"""

from __future__ import annotations

import csv
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

_CSV_FIELDS = [
    "timestamp", "violation_type", "license_plate",
    "speed_kmh", "confidence", "evidence_image", "location",
]


# ─────────────────────────────────────────────────────────────────────────────
# Evidence Capture
# ─────────────────────────────────────────────────────────────────────────────

class EvidenceCapture:
    """
    Saves video-frame snapshots as JPEG evidence files.

    Parameters
    ----------
    evidence_dir:
        Directory where evidence images are stored.
    quality:
        JPEG quality (1–100).
    """

    def __init__(
        self,
        evidence_dir: str = "data/evidence",
        quality: int = 90,
    ) -> None:
        self._dir     = Path(evidence_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._quality = quality
        self._count   = 0
        logger.info("EvidenceCapture: saving to %s", self._dir)

    def capture(
        self,
        frame: np.ndarray,
        violation_type: str,
        plate: str = "UNKNOWN",
        timestamp: Optional[datetime] = None,
        roi_bbox: Optional[tuple] = None,
    ) -> str:
        """
        Save *frame* (or its ROI) as a JPEG evidence file.

        Returns the absolute path of the saved image.
        """
        ts      = timestamp or datetime.now()
        ts_str  = ts.strftime("%Y%m%d_%H%M%S_%f")
        safe_vt = violation_type.replace(" ", "_").upper()
        safe_pl = "".join(c for c in plate if c.isalnum() or c in "_-")
        fname   = f"{safe_vt}_{safe_pl}_{ts_str}.jpg"
        fpath   = self._dir / fname

        img = frame
        if roi_bbox:
            x1, y1, x2, y2 = roi_bbox
            img = frame[max(0, y1):y2, max(0, x1):x2]
            if img.size == 0:
                img = frame

        # Stamp timestamp and violation type on the evidence image
        stamped = img.copy()
        stamp   = f"{ts.isoformat()} | {violation_type} | {plate}"
        cv2.putText(stamped, stamp, (5, stamped.shape[0] - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)

        cv2.imwrite(str(fpath), stamped, [cv2.IMWRITE_JPEG_QUALITY, self._quality])
        self._count += 1
        logger.debug("Evidence saved: %s", fpath)
        return str(fpath)

    @property
    def count(self) -> int:
        return self._count


# ─────────────────────────────────────────────────────────────────────────────
# Violation Logger
# ─────────────────────────────────────────────────────────────────────────────

class ViolationLogger:
    """
    Appends violation records to a CSV file and optionally to a JSON log.

    Parameters
    ----------
    log_dir:
        Directory for log files.
    csv_name / json_name:
        Filenames within *log_dir*.
    enable_json:
        Also write a line-delimited JSON (.jsonl) log alongside the CSV.
    """

    def __init__(
        self,
        log_dir: str = "data/logs",
        csv_name: str = "violations.csv",
        json_name: str = "violations.jsonl",
        enable_json: bool = True,
    ) -> None:
        self._dir  = Path(log_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

        self._csv_path  = self._dir / csv_name
        self._json_path = self._dir / json_name if enable_json else None

        self._init_csv()
        logger.info("ViolationLogger: logging to %s", self._dir)

    # ------------------------------------------------------------------
    def _init_csv(self) -> None:
        if not self._csv_path.exists():
            with open(self._csv_path, "w", newline="") as f:
                csv.DictWriter(f, fieldnames=_CSV_FIELDS).writeheader()

    # ------------------------------------------------------------------
    def log(
        self,
        violation_type: str,
        license_plate: str = "UNKNOWN",
        speed_kmh: Optional[float] = None,
        confidence: float = 1.0,
        evidence_path: str = "",
        location: str = "N/A",
        timestamp: Optional[datetime] = None,
    ) -> dict:
        """
        Write one violation record and return it as a dict.
        """
        ts  = timestamp or datetime.now()
        row = {
            "timestamp":      ts.strftime("%Y-%m-%d %H:%M:%S"),
            "violation_type": violation_type,
            "license_plate":  license_plate,
            "speed_kmh":      f"{speed_kmh:.1f}" if speed_kmh is not None else "",
            "confidence":     f"{confidence:.2f}",
            "evidence_image": evidence_path,
            "location":       location,
        }

        # CSV
        with open(self._csv_path, "a", newline="") as f:
            csv.DictWriter(f, fieldnames=_CSV_FIELDS).writerow(row)

        # JSON
        if self._json_path:
            with open(self._json_path, "a") as f:
                f.write(json.dumps(row) + "\n")

        logger.info("[VIOLATION] %s | plate=%s | speed=%s",
                    violation_type, license_plate, speed_kmh)
        return row

    # ------------------------------------------------------------------
    def get_all(self) -> list[dict]:
        """Return all records from the CSV as a list of dicts."""
        if not self._csv_path.exists():
            return []
        with open(self._csv_path, newline="") as f:
            return list(csv.DictReader(f))

    def get_recent(self, n: int = 20) -> list[dict]:
        return self.get_all()[-n:]

    @property
    def csv_path(self) -> Path:
        return self._csv_path
