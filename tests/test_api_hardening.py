from __future__ import annotations

import app.behavior.lesson_tracker as lesson_tracker
from app import create_app


def test_lesson_duration_uses_elapsed_time_not_poll_count(monkeypatch):
    now = [100.0]
    monkeypatch.setattr(lesson_tracker, "monotonic", lambda: now[0])
    tracker = lesson_tracker.LessonTracker()
    tracker.update({"brake_events": 0, "lane_offset": 0.0}, event_id="sample-1")
    tracker.update({"brake_events": 0, "lane_offset": 0.0}, event_id="sample-2")
    now[0] = 101.5

    summary = tracker.get_summary()
    assert summary["Duration (seconds)"] == 1
    assert summary["Duration (min)"] == 0
    assert summary["Samples"] == 2
    assert summary["Mistakes"] == 0


def test_tracker_deduplicates_events_and_supports_pause(monkeypatch):
    now = [100.0]
    monkeypatch.setattr(lesson_tracker, "monotonic", lambda: now[0])
    tracker = lesson_tracker.LessonTracker()
    assert tracker.update({"brake_events": 3}, event_id="same-event")
    assert not tracker.update({"brake_events": 3}, event_id="same-event")
    assert tracker.get_summary()["Samples"] == 1
    assert tracker.pause()
    now[0] = 110.0
    assert not tracker.update({"brake_events": 0}, event_id="paused-event")
    assert tracker.resume()
    now[0] = 115.0
    assert tracker.get_summary()["Duration (seconds)"] == 5


def test_dashboard_and_health_endpoints(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    client = create_app().test_client()
    assert client.get("/").status_code == 200
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.get_json()["status"] == "ok"


def test_dashboard_reads_do_not_ingest_telemetry(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    client = create_app().test_client()
    first = client.get("/api/telemetry").get_json()
    second = client.get("/api/telemetry").get_json()
    assert first["progress"]["Samples"] == 0
    assert second["progress"]["Samples"] == 0


def test_telemetry_ingestion_is_explicit_and_idempotent(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    client = create_app().test_client()
    payload = {"event_id": "vehicle-event-1", "speed": 42, "brake_events": 3, "lane_offset": 0.1}
    first = client.post("/api/telemetry", json=payload)
    duplicate = client.post("/api/telemetry", json=payload)
    assert first.status_code == 202
    assert first.get_json()["accepted"] is True
    assert duplicate.status_code == 200
    assert duplicate.get_json()["duplicate"] is True
    assert client.get("/api/session").get_json()["progress"]["Samples"] == 1


def test_session_lifecycle_endpoints(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    client = create_app().test_client()
    assert client.post("/api/session", json={"action": "pause"}).status_code == 200
    blocked = client.post("/api/telemetry", json={"event_id": "paused", "speed": 30})
    assert blocked.status_code == 409
    assert client.post("/api/session", json={"action": "resume"}).status_code == 200
    assert client.post("/api/session", json={"action": "end"}).status_code == 200
    assert client.post("/api/session", json={"action": "start"}).get_json()["progress"]["Samples"] == 0


def test_violation_api_rejects_invalid_payloads(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    client = create_app().test_client()
    assert client.post("/api/violations", data="not-json",
                       content_type="application/json").status_code == 400
    assert client.post("/api/violations", json={"speed_kmh": 900}).status_code == 400
    assert client.post("/api/violations", json={"confidence": 2}).status_code == 400
    assert client.get("/api/violations?n=0").status_code == 400
    assert client.get("/api/violations?n=not-a-number").status_code == 400
    assert client.post("/api/telemetry", json={"speed": float("nan"), "event_id": "bad"}).status_code == 400


def test_violation_storage_persists_and_deduplicates(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    client = create_app().test_client()
    payload = {
        "event_id": "violation-1", "violation_type": "SPEEDING",
        "license_plate": "TEST-123", "speed_kmh": 75, "confidence": 0.95,
    }
    response = client.post("/api/violations", json=payload)
    assert response.status_code == 201
    duplicate = client.post("/api/violations", json=payload)
    assert duplicate.status_code == 200
    assert duplicate.get_json()["duplicate"] is True

    # A new application instance reads the same SQLite-backed event history.
    second_client = create_app().test_client()
    stats = second_client.get("/api/violations/stats").get_json()
    assert stats["total"] == 1
    assert stats["by_type"]["SPEEDING"] == 1


def test_legacy_csv_history_is_migrated_to_sqlite(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    log_dir = tmp_path / "data" / "logs"
    log_dir.mkdir(parents=True)
    (log_dir / "violations.csv").write_text(
        "timestamp,violation_type,license_plate,speed_kmh,confidence,evidence_image,location\n"
        "2026-01-01 10:00:00,SPEEDING,TEST-1,72.0,0.9,,Hyderabad\n",
        encoding="utf-8",
    )
    client = create_app().test_client()
    rows = client.get("/api/violations").get_json()
    assert len(rows) == 1
    assert rows[0]["violation_type"] == "SPEEDING"
    assert rows[0]["license_plate"] == "TEST-1"
