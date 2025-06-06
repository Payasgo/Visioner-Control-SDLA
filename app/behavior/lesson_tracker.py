# app/behavior/lesson_tracker.py

class LessonTracker:
    def __init__(self):
        self.duration = 0  # in minutes
        self.mistakes = 0

    def update(self, new_data):
        self.duration += 1  # Simulate each loop as 1 minute
        if new_data.get("brake_events", 0) > 2 or abs(new_data.get("lane_offset", 0)) > 0.5:
            self.mistakes += 1

    def get_summary(self):
        return {
            "Duration (min)": self.duration,
            "Mistakes": self.mistakes,
            "Progress": "In Progress" if self.duration < 10 else "Completed"
        }
