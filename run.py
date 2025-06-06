# run.py

from app.main import start_app

if __name__ == "__main__":
    print("🚦 Running Visioner-Control-SDLA (Simulator Mode)")
    start_app(mode="simulator")  # Change to "obd" for real vehicle input
