import pyttsx3

class VoiceCoach:
    """
    Provides voice-based coaching based on telemetry input.
    """

    def __init__(self):
        self.engine = pyttsx3.init()

    def give_tip(self, tip_text: str):
        """
        Uses TTS to speak a coaching tip.
        """
        self.engine.say(tip_text)
        self.engine.runAndWait()

    def analyze_and_coach(self, telemetry_data: dict):
        """
        Applies rule-based coaching based on telemetry.
        :param telemetry_data: dict with keys like 'speed'
        """
        speed = telemetry_data.get('speed', 0)
        if speed > 60:
            self.give_tip("Please slow down. You are over the speed limit.")
