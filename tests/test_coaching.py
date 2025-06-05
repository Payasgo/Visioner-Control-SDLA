from modules.coaching import VoiceCoach

def test_voice_coach_speak(monkeypatch):
    engine_mock = type("EngineMock", (), {"say": lambda self, x: None, "runAndWait": lambda self: None})()
    monkeypatch.setattr("pyttsx3.init", lambda: engine_mock)
    coach = VoiceCoach()
    coach.give_tip("Test tip")
