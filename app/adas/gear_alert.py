# app/adas/gear_alert.py

from app.utils.config import CONFIG


class GearAdvisor:
    """Suggests gear changes based on current speed."""

    HIGH_SPEED_THRESHOLD: float = 40.0
    HIGH_SPEED_MIN_GEAR: int = 3

    def suggest(self, speed: float, gear: int) -> str:
        min_gear_speed: float = CONFIG["min_gear_change_speed"]

        if speed < min_gear_speed and gear > 2:
            return "Downshift for better control at low speed."
        if speed > self.HIGH_SPEED_THRESHOLD and gear < self.HIGH_SPEED_MIN_GEAR:
            return "Shift to a higher gear to save fuel."
        return "Gear is appropriate."
