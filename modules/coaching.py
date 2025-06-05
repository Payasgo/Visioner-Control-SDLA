import pyttsx3

class VoiceCoach:
    def __init__(self):
        self.engine = pyttsx3.init()

    def give_tip(self, tip_text):
        self.engine.say(tip_text)
        self.engine.runAndWait()

    def analyze_and_coach(self, telemetry_data):
        # Example logic for coaching based on telemetry
        speed = telemetry_data.get('speed', 0)
        if speed > 60:
            self.give_tip("Please slow down. You are over the speed limit.")
