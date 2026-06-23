# app/telemetry/simulator_interface.py

import random


class TelemetrySimulator:
    """Generates random but plausible driving telemetry for offline testing."""

    def get_data(self) -> dict:
        return {
            "speed": float(random.randint(10, 100)),
            "gear": random.choice([1, 2, 3, 4, 5]),
            "brake_events": random.randint(0, 5),
            "lane_offset": round(random.uniform(-1.0, 1.0), 2),
            "steering_angle": round(random.uniform(-30.0, 30.0), 2),
        }
