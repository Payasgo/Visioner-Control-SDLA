# tests/test_behavior.py

import pytest
from app.behavior.classifier import DriverClassifier
from app.behavior.voice_coach import VoiceCoach
from app.behavior.lesson_tracker import LessonTracker

def test_driver_classifier_beginner():
    classifier = DriverClassifier()
    result = classifier.classify({"speed": 25, "brake_events": 3})
    assert result == "Beginner"

def test_driver_classifier_medium():
    classifier = DriverClassifier()
    result = classifier.classify({"speed": 45, "brake_events": 1})
    assert result == "Medium"

def test_driver_classifier_pro():
    classifier = DriverClassifier()
    result = classifier.classify({"speed": 80, "brake_events": 0})
    assert result == "Pro"

def test_voice_coach_tip(capsys):
    coach = VoiceCoach()
    coach.give_tip("Beginner")
    captured = capsys.readouterr()
    assert "Keep your hands on the wheel" in captured.out

def test_lesson_tracker_updates():
    tracker = LessonTracker()
    data = {"brake_events": 3, "lane_offset": 0.6}
    tracker.update(data)
    summary = tracker.get_summary()
    assert summary["Mistakes"] == 1
    assert summary["Duration (min)"] == 1
