import random
import time

def get_simulated_data():
    return {
        "speed": round(random.uniform(0, 120), 2),
        "rpm": random.randint(600, 4000),
        "engine_temp": round(random.uniform(70, 120), 1),
        "fuel_level": round(random.uniform(0, 100), 1),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
