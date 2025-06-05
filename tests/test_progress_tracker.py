import os
import json
import tempfile
from modules.progress_tracker import LessonProgressTracker

def test_update_and_get_progress():
    with tempfile.TemporaryDirectory() as tempdir:
        filepath = os.path.join(tempdir, "progress.json")
        tracker = LessonProgressTracker(filepath=filepath)
        tracker.update_progress("Lesson 1", "Completed")
        progress = tracker.get_progress()
        assert progress["Lesson 1"] == "Completed"
