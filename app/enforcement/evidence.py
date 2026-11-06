"""Evidence image capture and SQLite-backed violation event storage."""

from __future__ import annotations

import csv
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class EvidenceCapture:
    """Save timestamped JPEG snapshots. The caller owns evidence retention policy."""

    def __init__(self, evidence_dir: str = "data/evidence", quality: int = 90) -> None:
        if not 1 <= quality <= 100:
            raise ValueError("quality must be between 1 and 100")
        self._dir = Path(evidence_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._quality = quality
        self._count = 0

    def capture(
        self, frame: np.ndarray, violation_type: str, plate: str = "UNKNOWN",
        timestamp: Optional[datetime] = None, roi_bbox: Optional[tuple] = None,
    ) -> str:
        if not isinstance(frame, np.ndarray) or frame.size == 0:
            raise ValueError("frame must be a non-empty NumPy array")
        ts = timestamp or datetime.now(timezone.utc)
        safe_vt = "".join(c for c in violation_type if c.isalnum() or c in "_-").upper() or "EVENT"
        safe_pl = "".join(c for c in plate if c.isalnum() or c in "_-") or "UNKNOWN"
        img = frame
        if roi_bbox:
            if len(roi_bbox) != 4:
                raise ValueError("roi_bbox must contain x1, y1, x2, y2")
            x1, y1, x2, y2 = (int(v) for v in roi_bbox)
            cropped = frame[max(0, y1):max(0, y2), max(0, x1):max(0, x2)]
            if cropped.size:
                img = cropped
        stamped = img.copy()
        cv2.putText(
            stamped, f"{ts.isoformat()} | {safe_vt} | {safe_pl}",
            (5, max(18, stamped.shape[0] - 8)), cv2.FONT_HERSHEY_SIMPLEX,
            0.45, (0, 255, 255), 1,
        )
        path = self._dir / f"{safe_vt}_{safe_pl}_{ts.strftime('%Y%m%d_%H%M%S_%f')}.jpg"
        if not cv2.imwrite(str(path), stamped, [cv2.IMWRITE_JPEG_QUALITY, self._quality]):
            raise OSError(f"could not write evidence image: {path}")
        self._count += 1
        logger.info("Evidence saved: %s", path)
        return str(path.resolve())

    @property
    def count(self) -> int:
        return self._count


class ViolationLogger:
    """SQLite event store with indexed, transactional writes and bounded reads."""

    def __init__(
        self, log_dir: str = "data/logs", csv_name: str = "violations.csv",
        json_name: str = "violations.jsonl", enable_json: bool = True,
        database_name: str = "violations.sqlite3",
    ) -> None:
        # csv_name/json_name/enable_json remain accepted for backwards-compatible callers.
        del csv_name, json_name, enable_json
        self._dir = Path(log_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._database_path = self._dir / database_name
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute("PRAGMA journal_mode = WAL")
            db.execute("""
                CREATE TABLE IF NOT EXISTS violations (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    violation_type TEXT NOT NULL,
                    license_plate TEXT NOT NULL,
                    speed_kmh REAL,
                    confidence REAL NOT NULL,
                    evidence_image TEXT NOT NULL,
                    location TEXT NOT NULL
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_violations_timestamp ON violations(timestamp)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_violations_type ON violations(violation_type)")
        self._migrate_legacy_csv()

    def _migrate_legacy_csv(self) -> None:
        """Import existing CSV records once so the storage upgrade preserves history."""
        legacy_path = self._dir / "violations.csv"
        if not legacy_path.exists():
            return
        with self._connect() as db:
            if db.execute("SELECT COUNT(*) FROM violations").fetchone()[0]:
                return
            with legacy_path.open(newline="", encoding="utf-8") as source:
                for old in csv.DictReader(source):
                    raw_timestamp = old.get("timestamp") or datetime.now(timezone.utc).isoformat()
                    try:
                        parsed = datetime.fromisoformat(raw_timestamp)
                    except ValueError:
                        parsed = datetime.now(timezone.utc)
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=timezone.utc)
                    raw_speed = old.get("speed_kmh")
                    try:
                        speed = float(raw_speed) if raw_speed not in (None, "") else None
                    except (TypeError, ValueError):
                        speed = None
                    try:
                        confidence = float(old.get("confidence") or 1.0)
                    except (TypeError, ValueError):
                        confidence = 1.0
                    db.execute(
                        """INSERT OR IGNORE INTO violations
                        (id, timestamp, violation_type, license_plate, speed_kmh, confidence, evidence_image, location)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (str(uuid.uuid4()), parsed.astimezone(timezone.utc).isoformat(),
                         old.get("violation_type") or "UNKNOWN", old.get("license_plate") or "UNKNOWN",
                         speed, min(max(confidence, 0.0), 1.0), old.get("evidence_image") or "",
                         old.get("location") or "N/A"),
                    )

    def log(
        self, violation_type: str, license_plate: str = "UNKNOWN",
        speed_kmh: Optional[float] = None, confidence: float = 1.0,
        evidence_path: str = "", location: str = "N/A",
        timestamp: Optional[datetime] = None, event_id: Optional[str] = None,
    ) -> dict:
        ts = timestamp or datetime.now(timezone.utc)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        row = {
            "id": event_id or str(uuid.uuid4()),
            "timestamp": ts.astimezone(timezone.utc).isoformat(),
            "violation_type": violation_type,
            "license_plate": license_plate,
            "speed_kmh": float(speed_kmh) if speed_kmh is not None else None,
            "confidence": float(confidence),
            "evidence_image": evidence_path,
            "location": location,
        }
        with self._connect() as db:
            db.execute(
                """INSERT INTO violations
                (id, timestamp, violation_type, license_plate, speed_kmh, confidence, evidence_image, location)
                VALUES (:id, :timestamp, :violation_type, :license_plate, :speed_kmh, :confidence, :evidence_image, :location)""",
                row,
            )
        logger.info("Violation recorded: id=%s type=%s", row["id"], violation_type)
        return row

    def get_all(self) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM violations ORDER BY timestamp, rowid").fetchall()
        return [dict(row) for row in rows]

    def get_recent(self, n: int = 20) -> list[dict]:
        if not 1 <= n <= 1000:
            raise ValueError("n must be between 1 and 1000")
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM violations ORDER BY timestamp DESC, rowid DESC LIMIT ?", (n,)
            ).fetchall()
        return [dict(row) for row in reversed(rows)]

    def get_stats(self) -> dict:
        with self._connect() as db:
            total = db.execute("SELECT COUNT(*) FROM violations").fetchone()[0]
            counts = db.execute(
                "SELECT violation_type, COUNT(*) AS count FROM violations GROUP BY violation_type"
            ).fetchall()
        return {"total": total, "by_type": {row["violation_type"]: row["count"] for row in counts}}

    def get_by_id(self, event_id: str) -> dict | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM violations WHERE id = ?", (event_id,)).fetchone()
        return dict(row) if row else None

    @property
    def database_path(self) -> Path:
        return self._database_path
