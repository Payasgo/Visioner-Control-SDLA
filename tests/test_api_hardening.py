from __future__ import annotations

import app.behavior.lesson_tracker as lesson_tracker
from app import create_app


def test_lesson_duration_uses_elapsed_time_not_poll_count(monkeypatch):
    now = [100.0]
    monkeypatch.setattr(lesson_tracker, "monotonic", lambda: now[0])
    tracker = lesson_tracker.LessonTracker()
    tracker.update({"brake_events": 0, "lane_offset": 0.0})
    tracker.update({"brake_events": 0, "lane_offset": 0.0})
    now[0] = 101.5

    summary = tracker.get_summary()
    assert summary["Duration (seconds)"] == 1
    assert summary["Duration (min)"] == 0
    assert summary["Samples"] == 2
    assert summary["Mistakes"] == 0


def test_dashboard_and_health_endpoints(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    client = create_app().test_client()

    assert client.get("/").status_code == 200
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.get_json()["status"] == "ok"


def test_violation_api_rejects_invalid_payloads(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    client = create_app().test_client()

    assert client.post("/api/violations", data="not-json",
                       content_type="application/json").status_code == 400
    assert client.post("/api/violations", json={"speed_kmh": 900}).status_code == 400
    assert client.post("/api/violations", json={"confidence": 2}).status_code == 400
    assert client.get("/api/violations?n=0").status_code == 400


def test_violation_api_accepts_valid_payload_and_updates_stats(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    client = create_app().test_client()

    response = client.post(
        "/api/violations",
        json={
            "violation_type": "SPEEDING",
            "license_plate": "TEST-123",
            "speed_kmh": 75,
            "confidence": 0.95,
        },
    )
    assert response.status_code == 201
    stats = client.get("/api/violations/stats").get_json()
    assert stats["total"] == 1
    assert stats["by_type"]["SPEEDING"] == 1
