# modules/coaching.py

import logging

logger = logging.getLogger(__name__)


class VoiceCoach:
    """
    Provides coaching based on telemetry input.

    TTS (pyttsx3) is optional. If it is unavailable or running headlessly,
    the coach falls back to logging without crashing.
    """

    def __init__(self) -> None:
        self._engine = None
        try:
            import pyttsx3  # type: ignore

            self._engine = pyttsx3.init()
        except Exception as exc:
            logger.warning("TTS unavailable, falling back to log output: %s", exc)

    def give_tip(self, tip_text: str) -> None:
        """Speak *tip_text* via TTS, or log it if TTS is unavailable."""
        if self._engine is not None:
            try:
                self._engine.say(tip_text)
                self._engine.runAndWait()
                return
            except Exception as exc:
                logger.warning("TTS say() failed: %s", exc)
        logger.info("[Coach] %s", tip_text)

    def analyze_and_coach(self, telemetry_data: dict) -> None:
        """Apply rule-based coaching from live telemetry."""
        speed: float = telemetry_data.get("speed", 0)
        if speed > 60:
            self.give_tip("Please slow down. You are over the speed limit.")
