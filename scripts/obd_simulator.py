# scripts/obd_simulator.py

import random


def get_vehicle_data() -> dict:
    """Return a dict of simulated OBD-II readings."""
    return {
        "speed": float(random.randint(20, 80)),
        "rpm": random.randint(1000, 4000),
        "gear": random.randint(1, 5),
        "brake": random.choice([True, False]),
    }
