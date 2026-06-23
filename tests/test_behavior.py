# tests/test_behavior.py

from app.behavior.classifier import DriverClassifier
from app.behavior.lesson_tracker import LessonTracker
from app.behavior.voice_coach import VoiceCoach


# ── DriverClassifier ──────────────────────────────────────────────────────────

def test_driver_classifier_beginner():
    classifier = DriverClassifier()
    result = classifier.classify({"speed": 25, "brake_events": 3})
    assert result == "Beginner"


def test_driver_classifier_medium_low_speed():
    classifier = DriverClassifier()
    result = classifier.classify({"speed": 45, "brake_events": 1})
    assert result == "Medium"


def test_driver_classifier_medium_high_brakes():
    """High speed but many brakes → still Medium (not Pro)."""
    classifier = DriverClassifier()
    result = classifier.classify({"speed": 70, "brake_events": 3})
    assert result == "Medium"


def test_driver_classifier_pro():
    classifier = DriverClassifier()
    result = classifier.classify({"speed": 80, "brake_events": 0})
    assert result == "Pro"


def test_driver_classifier_defaults():
    """Missing keys should not raise."""
    classifier = DriverClassifier()
    result = classifier.classify({})
    assert result in {"Beginner", "Medium", "Pro"}


# ── VoiceCoach ────────────────────────────────────────────────────────────────

def test_voice_coach_tip(capsys):
    coach = VoiceCoach()
    coach.give_tip("Beginner")
    captured = capsys.readouterr()
    assert "Keep your hands on the wheel" in captured.out


def test_voice_coach_get_tip():
    coach = VoiceCoach()
    tip = coach.get_tip("Pro")
    assert "overtaking" in tip.lower()


def test_voice_coach_unknown_level():
    coach = VoiceCoach()
    tip = coach.get_tip("Unknown")
    assert tip == "Drive safely!"


# ── LessonTracker ─────────────────────────────────────────────────────────────

def test_lesson_tracker_records_mistake():
    tracker = LessonTracker()
    data = {"brake_events": 3, "lane_offset": 0.6}
    tracker.update(data)
    summary = tracker.get_summary()
    assert summary["Mistakes"] == 1
    assert summary["Duration (min)"] == 1


def test_lesson_tracker_no_mistakes():
    tracker = LessonTracker()
    data = {"brake_events": 1, "lane_offset": 0.2}
    tracker.update(data)
    summary = tracker.get_summary()
    assert summary["Mistakes"] == 0


def test_lesson_tracker_progress_in_progress():
    tracker = LessonTracker()
    tracker.update({"brake_events": 0, "lane_offset": 0.0})
    assert tracker.get_summary()["Progress"] == "In Progress"


def test_lesson_tracker_progress_complete():
    tracker = LessonTracker()
    for _ in range(10):
        tracker.update({"brake_events": 0, "lane_offset": 0.0})
    summary = tracker.get_summary()
    assert summary["Progress"] == "Completed"
