# app/telemetry/obd_interface.py
#
# NOTE: Mock structure. Real OBD-II integration uses pyOBD or an ELM327 adapter.


class OBDConnectionError(RuntimeError):
    """Raised when an OBD operation is attempted without an active connection."""


class OBDInterface:
    """Thin wrapper around an OBD-II serial connection."""

    def __init__(self, port: str = "/dev/ttyUSB0") -> None:
        self.port = port
        self.connected: bool = False

    def connect(self) -> None:
        print(f"[OBD] Connecting to vehicle at {self.port}")
        # TODO: replace with real pyOBD / ELM327 handshake
        self.connected = True

    def disconnect(self) -> None:
        self.connected = False
        print("[OBD] Disconnected.")

    def get_data(self) -> dict:
        if not self.connected:
            raise OBDConnectionError("OBD not connected. Call connect() first.")
        # TODO: replace with real PID queries
        return {
            "speed": 55.0,
            "gear": 3,
            "brake_events": 1,
            "lane_offset": 0.1,
            "steering_angle": -2.5,
        }
