import json
import os

class LessonProgressTracker:
    """
    Tracks the lesson progress of the driver in a local JSON file.
    """

    def __init__(self, filepath='data/progress.json'):
        self.filepath = filepath
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                json.dump({}, f)

    def update_progress(self, lesson: str, status: str):
        """
        Updates the lesson status (e.g., completed, pending).
        """
        with open(self.filepath, 'r+') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
            data[lesson] = status
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

    def get_progress(self) -> dict:
        """
        Returns all lesson progress data.
        """
        with open(self.filepath) as f:
            return json.load(f)
