from app.behavior.classifier import DriverClassifier
from app.behavior.lesson_tracker import LessonTracker
from app.behavior.voice_coach import VoiceCoach


def test_classifier_does_not_reward_high_speed():
    classifier = DriverClassifier()
    assert classifier.classify({"speed": 95}) == "Unknown"


def test_classifier_uses_behaviour_signals():
    classifier = DriverClassifier()
    assert classifier.classify({"brake_events": 0, "lane_offset": 0.1}) == "Pro"
    assert classifier.classify({"brake_events": 2, "lane_offset": 0.1}) == "Medium"
    assert classifier.classify({"brake_events": 4, "lane_offset": 0.8}) == "Beginner"


def test_classifier_penalizes_speed_only_when_limit_is_known():
    classifier = DriverClassifier()
    safe = classifier.classify({"brake_events": 0, "lane_offset": 0.1, "speed": 90})
    over_limit = classifier.classify({
        "brake_events": 0, "lane_offset": 0.1, "speed": 90, "speed_limit": 50,
    })
    assert safe == "Pro"
    assert over_limit == "Medium"


def test_voice_coach_tip(capsys):
    coach = VoiceCoach()
    coach.give_tip("Beginner")
    assert "Keep your hands on the wheel" in capsys.readouterr().out


def test_voice_coach_get_tip():
    assert "overtaking" in VoiceCoach().get_tip("Pro").lower()


def test_voice_coach_unknown_level():
    assert VoiceCoach().get_tip("Unknown") == "Drive safely!"


def test_lesson_tracker_records_one_mistake_per_sample():
    tracker = LessonTracker()
    tracker.update({"brake_events": 3, "lane_offset": 0.6})
    summary = tracker.get_summary()
    assert summary["Mistakes"] == 1
    assert summary["Duration (min)"] == 0
    assert summary["Samples"] == 1


def test_lesson_tracker_no_mistakes():
    tracker = LessonTracker()
    tracker.update({"brake_events": 1, "lane_offset": 0.2})
    assert tracker.get_summary()["Mistakes"] == 0


def test_lesson_tracker_progress_in_progress():
    tracker = LessonTracker()
    assert tracker.get_summary()["Progress"] == "In Progress"


def test_lesson_tracker_progress_complete(monkeypatch):
    now = [100.0]
    monkeypatch.setattr("app.behavior.lesson_tracker.monotonic", lambda: now[0])
    tracker = LessonTracker()
    for index in range(10):
        tracker.update({"brake_events": 0, "lane_offset": 0.0}, event_id=str(index))
    now[0] += tracker.COMPLETION_DURATION_SECONDS
    assert tracker.get_summary()["Progress"] == "Completed"
