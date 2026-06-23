# modules/safety_parking.py


def auto_correct(steering_angle: float, safety_threshold: float = 15.0) -> float:
    """
    Halves the steering angle when it exceeds *safety_threshold* degrees.

    Args:
        steering_angle:   Current steering angle in degrees.
        safety_threshold: Maximum safe absolute angle before correction kicks in.

    Returns:
        The (possibly corrected) steering angle.
    """
    if abs(steering_angle) > safety_threshold:
        return steering_angle * 0.5
    return steering_angle


def parking_logic(parking_sensor_data: dict) -> str:
    """
    Returns a parking assist message based on proximity sensor data.

    Args:
        parking_sensor_data: Dict expected to contain 'distance' (cm).
    """
    distance = parking_sensor_data.get("distance")
    if distance is None:
        return "Parking sensor unavailable."
    if distance < 10:
        return "Parking assist: Please stop, obstacle detected."
    return "Parking clear."
