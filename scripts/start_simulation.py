# scripts/start_simulation.py
"""
Starts Visioner-Control-SDLA in simulator mode.
Simulates vehicle telemetry, runs ADAS & behaviour logic, and optionally serves the UI.
"""

from app.main import start_app


def main() -> None:
    print("Starting Visioner-Control-SDLA in SIMULATION mode...")
    start_app(mode="simulator")


if __name__ == "__main__":
    main()
