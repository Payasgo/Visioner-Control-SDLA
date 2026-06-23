# app/hardware/android_auto.py


class AndroidAutoInterface:
    """Stub for Android Auto communication."""

    def connect(self) -> bool:
        print("[AndroidAuto] Initializing communication...")
        return True

    def send_alert(self, message: str) -> None:
        print(f"[AndroidAuto Alert] {message}")
