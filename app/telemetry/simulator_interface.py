# app/telemetry/simulator_interface.py

import random

class TelemetrySimulator:
    def get_data(self):
        return {
            "speed": random.randint(10, 100),
            "gear": random.choice([1, 2, 3, 4, 5]),
            "brake_events": random.randint(0, 5),
            "lane_offset": round(random.uniform(-1.0, 1.0), 2),
            "steering_angle": round(random.uniform(-30, 30), 2)
        }
