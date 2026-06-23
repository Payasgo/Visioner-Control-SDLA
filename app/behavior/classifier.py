# app/behavior/classifier.py


class DriverClassifier:
    """
    Classifies driver skill level from telemetry data.

    Rules (in priority order):
      Beginner – speed < 30 km/h AND brake_events > 2
      Pro      – speed >= 60 km/h AND brake_events <= 1
      Medium   – everything else
    """

    def classify(self, telemetry_data: dict) -> str:
        speed: float = telemetry_data.get("speed", 0)
        sudden_brakes: int = telemetry_data.get("brake_events", 0)

        if speed < 30 and sudden_brakes > 2:
            return "Beginner"
        if speed >= 60 and sudden_brakes <= 1:
            return "Pro"
        return "Medium"
