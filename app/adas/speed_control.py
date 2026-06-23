# app/adas/speed_control.py

from app.utils.config import CONFIG


class SpeedController:
    """Warns the driver when speed exceeds the limit for their skill level."""

    def adjust(self, current_speed: float, skill_level: str) -> str | None:
        limits: dict[str, float] = {
            "Beginner": CONFIG["max_speed_beg"],
            "Medium": CONFIG["max_speed_med"],
            "Pro": CONFIG["max_speed_pro"],
        }

        max_speed = limits.get(skill_level)
        if max_speed is None:
            return None  # Unknown skill level; no action

        if current_speed > max_speed:
            msg = f"[ADAS] Speed Warning: Reduce speed below {max_speed:.0f} km/h."
            print(msg)
            return msg

        return None
