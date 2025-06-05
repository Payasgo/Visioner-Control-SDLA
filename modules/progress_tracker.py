import json
import os

class LessonProgressTracker:
    def __init__(self, filepath='data/progress.json'):
        self.filepath = filepath
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                json.dump({}, f)

    def update_progress(self, lesson, status):
        with open(self.filepath, 'r+') as f:
            data = json.load(f)
            data[lesson] = status
            f.seek(0)
            json.dump(data, f)
            f.truncate()

    def get_progress(self):
        with open(self.filepath) as f:
            return json.load(f)
