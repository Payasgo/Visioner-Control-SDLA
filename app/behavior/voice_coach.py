# app/behavior/voice_coach.py

TIPS: dict[str, str] = {
    "Beginner": "Keep your hands on the wheel and eyes on the road.",
    "Medium": "Watch your mirrors and maintain a steady pace.",
    "Pro": "Excellent. Consider practicing overtaking safely.",
}

_DEFAULT_TIP = "Drive safely!"


class VoiceCoach:
    """Returns text-based coaching tips (TTS handled at a higher layer)."""

    def get_tip(self, skill_level: str) -> str:
        return TIPS.get(skill_level, _DEFAULT_TIP)

    def give_tip(self, skill_level: str) -> None:
        print("[Coach] " + self.get_tip(skill_level))
