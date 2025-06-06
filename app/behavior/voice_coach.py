# app/behavior/voice_coach.py

class VoiceCoach:
    def give_tip(self, skill_level):
        tips = {
            "Beginner": "Keep your hands on the wheel and eyes on the road.",
            "Medium": "Watch your mirrors and maintain a steady pace.",
            "Pro": "Excellent. Consider practicing overtaking safely."
        }
        print("[Coach] " + tips.get(skill_level, "Drive safely!"))
