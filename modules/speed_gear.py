def check_speed_limit(speed, city_traffic=True):
    limit = 50 if city_traffic else 90
    if speed > limit:
        return f"Speed limit exceeded! Limit is {limit} km/h"
    return None

def gear_alert(current_gear, speed):
    if current_gear == 1 and speed > 30:
        return "Consider shifting up"
    if current_gear > 3 and speed < 20:
        return "Consider shifting down"
    return None
