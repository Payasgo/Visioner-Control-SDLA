# app/behavior/lesson_tracker.py


class LessonTracker:
    """Accumulates per-loop driving metrics and produces a summary."""

    MISTAKE_BRAKE_THRESHOLD: int = 2
    MISTAKE_LANE_THRESHOLD: float = 0.5
    COMPLETION_DURATION: int = 10  # minutes

    def __init__(self) -> None:
        self.duration: int = 0   # simulated minutes (one update == one minute)
        self.mistakes: int = 0

    def update(self, new_data: dict) -> None:
        self.duration += 1
        brakes: int = new_data.get("brake_events", 0)
        offset: float = new_data.get("lane_offset", 0.0)
        if brakes > self.MISTAKE_BRAKE_THRESHOLD or abs(offset) > self.MISTAKE_LANE_THRESHOLD:
            self.mistakes += 1

    def get_summary(self) -> dict:
        progress = (
            "Completed" if self.duration >= self.COMPLETION_DURATION else "In Progress"
        )
        return {
            "Duration (min)": self.duration,
            "Mistakes": self.mistakes,
            "Progress": progress,
        }
