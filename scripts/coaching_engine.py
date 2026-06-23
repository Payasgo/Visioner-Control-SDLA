# scripts/coaching_engine.py

import logging

logger = logging.getLogger(__name__)

_engine = None


def _get_engine():
    """Lazy-initialise pyttsx3 so imports don't crash on headless systems."""
    global _engine
    if _engine is None:
        try:
            import pyttsx3  # type: ignore

            _engine = pyttsx3.init()
        except Exception as exc:
            logger.warning("TTS unavailable: %s", exc)
    return _engine


def speak(text: str) -> None:
    engine = _get_engine()
    if engine is not None:
        try:
            engine.say(text)
            engine.runAndWait()
            return
        except Exception as exc:
            logger.warning("TTS say() failed: %s", exc)
    logger.info("[Coach] %s", text)


def coaching_advice(driver_state: str, vehicle_data: dict) -> None:
    speed: float = vehicle_data.get("speed", 0)
    gear: int = vehicle_data.get("gear", 1)

    if driver_state == "Drowsy":
        speak("You look drowsy. Please take a break.")
    if speed > 60:
        speak("Reduce speed in city traffic.")
    if speed < 30 and gear > 3:
        speak("Shift to lower gear for better control.")
