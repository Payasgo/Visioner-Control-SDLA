# app/hardware/android_auto.py

class AndroidAutoInterface:
    def connect(self):
        print("[AndroidAuto] Initializing communication...")
        return True

    def send_alert(self, message):
        print(f"[AndroidAuto Alert] {message}")
