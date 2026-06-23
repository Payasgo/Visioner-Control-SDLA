# app/routes.py

from flask import Flask, jsonify, render_template

from app.behavior.classifier import DriverClassifier
from app.behavior.lesson_tracker import LessonTracker
from app.behavior.voice_coach import VoiceCoach
from app.telemetry.simulator_interface import TelemetrySimulator


def register_routes(app: Flask) -> None:
    """Attach all routes to *app*.

    State objects are created once per application instance (not at import
    time) so they are properly scoped to the app and don't leak between tests.
    """
    simulator = TelemetrySimulator()
    classifier = DriverClassifier()
    tracker = LessonTracker()
    coach = VoiceCoach()

    @app.route("/")
    def dashboard():
        data = simulator.get_data()
        skill = classifier.classify(data)
        tracker.update(data)
        tip = coach.get_tip(skill)
        progress = tracker.get_summary()
        return render_template(
            "dashboard.html", skill=skill, tip=tip, progress=progress
        )

    @app.route("/api/telemetry")
    def api_telemetry():
        data = simulator.get_data()
        skill = classifier.classify(data)
        # Note: tracker is NOT updated here to avoid double-counting when the
        # JS dashboard polls this endpoint while the user also views the HTML page.
        return jsonify(
            {
                "telemetry": data,
                "skill": skill,
                "tip": coach.get_tip(skill),
                "progress": tracker.get_summary(),
            }
        )

    @app.route("/api/health")
    def api_health():
        return jsonify({"status": "ok"})
