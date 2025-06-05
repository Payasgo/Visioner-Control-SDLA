def auto_correct(steering_angle: float, safety_threshold: float = 15) -> float:
    """
    Applies a correction to the steering angle if it exceeds safe bounds.
    """
    if abs(steering_angle) > safety_threshold:
        return steering_angle * 0.5
    return steering_angle

def parking_logic(parking_sensor_data: dict) -> str:
    """
    Provides parking feedback based on proximity sensor data.
    """
    distance = parking_sensor_data.get('distance')
    if distance is not None and distance < 10:
        return "Parking assist: Please stop, obstacle detected"
    return "Parking clear"
