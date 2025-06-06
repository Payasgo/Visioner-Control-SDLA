# app/behavior/classifier.py

class DriverClassifier:
    def classify(self, telemetry_data):
        speed = telemetry_data.get("speed", 0)
        sudden_brakes = telemetry_data.get("brake_events", 0)

        if speed < 30 and sudden_brakes > 2:
            return "Beginner"
        elif speed < 60:
            return "Medium"
        else:
            return "Pro"
