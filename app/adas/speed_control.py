# app/adas/speed_control.py

class SpeedController:
    def adjust(self, current_speed, skill_level):
        if skill_level == "Beginner" and current_speed > 40:
            print("[ADAS] Speed Warning: Please slow down.")
        elif skill_level == "Medium" and current_speed > 60:
            print("[ADAS] Maintain moderate speed.")
        elif skill_level == "Pro" and current_speed > 80:
            print("[ADAS] High-speed detected. Be cautious.")
