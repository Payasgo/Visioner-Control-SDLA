"""Session lifecycle and event-based driving lesson tracking."""

from __future__ import annotations

from threading import RLock
from time import monotonic
from typing import Any


class LessonTracker:
    """Track one lesson; only unique ingested telemetry events affect counters."""

    MISTAKE_BRAKE_THRESHOLD = 2
    MISTAKE_LANE_THRESHOLD = 0.5
    COMPLETION_DURATION_SECONDS = 10 * 60

    def __init__(self) -> None:
        self._lock = RLock()
        self._started_at: float | None = monotonic()
        self._ended_at: float | None = None
        self._paused_at: float | None = None
        self._paused_seconds = 0.0
        self._mistakes = 0
        self._samples = 0
        self._event_ids: set[str] = set()

    def start(self) -> None:
        """Start a fresh lesson and clear the previous lesson's counters."""
        with self._lock:
            self._started_at = monotonic()
            self._ended_at = None
            self._paused_at = None
            self._paused_seconds = 0.0
            self._mistakes = 0
            self._samples = 0
            self._event_ids.clear()

    def pause(self) -> bool:
        with self._lock:
            if self._started_at is None or self._ended_at is not None or self._paused_at is not None:
                return False
            self._paused_at = monotonic()
            return True

    def resume(self) -> bool:
        with self._lock:
            if self._paused_at is None or self._ended_at is not None:
                return False
            self._paused_seconds += max(0.0, monotonic() - self._paused_at)
            self._paused_at = None
            return True

    def end(self) -> bool:
        with self._lock:
            if self._started_at is None or self._ended_at is not None:
                return False
            now = monotonic()
            if self._paused_at is not None:
                self._paused_seconds += max(0.0, now - self._paused_at)
                self._paused_at = None
            self._ended_at = now
            return True

    def update(self, new_data: dict[str, Any], event_id: str | None = None) -> bool:
        """Ingest one sample. Duplicate event IDs and inactive sessions are ignored."""
        if not isinstance(new_data, dict):
            raise TypeError("telemetry sample must be a dictionary")
        with self._lock:
            if self._started_at is None or self._ended_at is not None or self._paused_at is not None:
                return False
            if event_id:
                if event_id in self._event_ids:
                    return False
                self._event_ids.add(event_id)
            self._samples += 1
            brakes = int(new_data.get("brake_events", 0) or 0)
            offset = float(new_data.get("lane_offset", 0.0) or 0.0)
            if brakes > self.MISTAKE_BRAKE_THRESHOLD or abs(offset) > self.MISTAKE_LANE_THRESHOLD:
                self._mistakes += 1
            return True

    def get_summary(self) -> dict[str, Any]:
        with self._lock:
            if self._started_at is None:
                elapsed_seconds = 0
                status = "Not Started"
            else:
                end = self._ended_at or self._paused_at or monotonic()
                elapsed_seconds = max(0, int(end - self._started_at - self._paused_seconds))
                status = "Ended" if self._ended_at is not None else (
                    "Paused" if self._paused_at is not None else "In Progress"
                )
            completed = elapsed_seconds >= self.COMPLETION_DURATION_SECONDS
            return {
                "Duration (min)": elapsed_seconds // 60,
                "Duration (seconds)": elapsed_seconds,
                "Mistakes": self._mistakes,
                "Samples": self._samples,
                "Status": status,
                "Progress": "Completed" if completed else status,
            }
