# scripts/start_simulation.py

"""
Starts the Visioner-Control-SDLA system in simulator mode.
Simulates vehicle telemetry, processes ADAS & behavior logic, and optionally serves UI.
"""

from app.main import start_app

def main():
    print("🚗 Starting Visioner-Control-SDLA in SIMULATION mode...")
    start_app(mode="simulator")

if __name__ == "__main__":
    main()
