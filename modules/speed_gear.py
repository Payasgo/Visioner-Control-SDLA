# modules/speed_gear.py


def check_speed_limit(speed: float, city_traffic: bool = True) -> str | None:
    """
    Returns a warning string when *speed* exceeds the applicable limit,
    or None when within limits.

    Args:
        speed:        Current vehicle speed in km/h.
        city_traffic: True for city limit (50 km/h), False for highway (90 km/h).
    """
    limit: float = 50.0 if city_traffic else 90.0
    if speed > limit:
        return f"Speed limit exceeded! Current: {speed:.0f} km/h, Limit: {limit:.0f} km/h."
    return None


def gear_alert(current_gear: int, speed: float) -> str | None:
    """
    Suggests a gear shift based on speed and current gear.

    Returns a hint string, or None when no change is needed.
    """
    if current_gear == 1 and speed > 30:
        return "Consider shifting up."
    if current_gear > 3 and speed < 20:
        return "Consider shifting down."
    return None
