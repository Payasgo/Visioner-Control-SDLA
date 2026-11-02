# app/behavior/lesson_tracker.py

from __future__ import annotations

from time import monotonic
from typing import Any


class LessonTracker:
    """Track elapsed wall-clock time and driving mistakes for one lesson."""

    MISTAKE_BRAKE_THRESHOLD = 2
    MISTAKE_LANE_THRESHOLD = 0.5
    COMPLETION_DURATION_SECONDS = 10 * 60

    def __init__(self) -> None:
        self._started_at = monotonic()
        self._mistakes = 0
        self._samples = 0

    def update(self, new_data: dict[str, Any]) -> None:
        """Record a telemetry sample without treating polls as elapsed minutes."""
        self._samples += 1
        brakes = int(new_data.get("brake_events", 0) or 0)
        offset = float(new_data.get("lane_offset", 0.0) or 0.0)
        if brakes > self.MISTAKE_BRAKE_THRESHOLD or abs(offset) > self.MISTAKE_LANE_THRESHOLD:
            self._mistakes += 1

    def get_summary(self) -> dict[str, Any]:
        elapsed_seconds = max(0, int(monotonic() - self._started_at))
        return {
            "Duration (min)": elapsed_seconds // 60,
            "Duration (seconds)": elapsed_seconds,
            "Mistakes": self._mistakes,
            "Samples": self._samples,
            "Progress": (
                "Completed"
                if elapsed_seconds >= self.COMPLETION_DURATION_SECONDS
                else "In Progress"
            ),
        }
