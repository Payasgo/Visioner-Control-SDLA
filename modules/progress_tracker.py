# modules/progress_tracker.py

import json
import os


class LessonProgressTracker:
    """Persists lesson progress to a local JSON file."""

    def __init__(self, filepath: str = "data/progress.json") -> None:
        self.filepath = filepath
        dir_name = os.path.dirname(filepath)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        if not os.path.exists(filepath):
            with open(filepath, "w") as fh:
                json.dump({}, fh)

    def _read(self) -> dict:
        with open(self.filepath) as fh:
            try:
                return json.load(fh)
            except json.JSONDecodeError:
                return {}

    def update_progress(self, lesson: str, status: str) -> None:
        """Set *lesson* to *status* (e.g. 'completed', 'pending')."""
        data = self._read()
        data[lesson] = status
        with open(self.filepath, "w") as fh:
            json.dump(data, fh, indent=2)

    def get_progress(self) -> dict:
        return self._read()
