"""Conservative rule-based driving feedback from observed behaviour."""


class DriverClassifier:
    """Estimate a coaching band; speed alone is never treated as driving skill.

    This is a simple heuristic, not a validated driver assessment or safety score.
    """

    def classify(self, telemetry_data: dict) -> str:
        if not isinstance(telemetry_data, dict):
            return "Unknown"

        has_behaviour_data = any(
            key in telemetry_data for key in ("brake_events", "lane_offset", "harsh_acceleration")
        )
        if not has_behaviour_data:
            return "Unknown"

        score = 100
        brakes = telemetry_data.get("brake_events", 0)
        lane_offset = telemetry_data.get("lane_offset", 0.0)
        acceleration = telemetry_data.get("harsh_acceleration", 0)

        if isinstance(brakes, (int, float)) and not isinstance(brakes, bool):
            score -= min(max(brakes, 0), 5) * 8
        if isinstance(lane_offset, (int, float)) and not isinstance(lane_offset, bool):
            if abs(lane_offset) > 0.5:
                score -= 25
        if isinstance(acceleration, (int, float)) and not isinstance(acceleration, bool):
            score -= min(max(acceleration, 0), 5) * 5

        speed = telemetry_data.get("speed")
        speed_limit = telemetry_data.get("speed_limit")
        if (
            isinstance(speed, (int, float)) and not isinstance(speed, bool)
            and isinstance(speed_limit, (int, float)) and not isinstance(speed_limit, bool)
            and speed > speed_limit
        ):
            score -= 20

        if score < 60:
            return "Beginner"
        if score < 85:
            return "Medium"
        return "Pro"
