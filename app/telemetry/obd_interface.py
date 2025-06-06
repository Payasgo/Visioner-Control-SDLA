# app/telemetry/obd_interface.py

# NOTE: This is a mock structure; actual OBD-II integration uses pyOBD or ELM327 device

class OBDInterface:
    def __init__(self, port="/dev/ttyUSB0"):
        self.port = port
        self.connected = False

    def connect(self):
        print(f"[OBD] Connecting to vehicle at {self.port}")
        self.connected = True

    def get_data(self):
        if not self.connected:
            raise Exception("OBD not connected.")
        # Simulate reading real-time vehicle data
        return {
            "speed": 55,
            "gear": 3,
            "brake_events": 1,
            "lane_offset": 0.1,
            "steering_angle": -2.5
        }
