# app/adas/gear_alert.py

class GearAdvisor:
    def suggest(self, speed, gear):
        if speed < 20 and gear > 2:
            return "Lower your gear for better control."
        elif speed > 40 and gear < 3:
            return "Consider shifting to a higher gear."
        return "Gear is appropriate."
