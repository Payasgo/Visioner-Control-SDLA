def auto_correct(steering_angle, safety_threshold=15):
    if abs(steering_angle) > safety_threshold:
        corrected_angle = steering_angle * 0.5
        return corrected_angle
    return steering_angle

def parking_logic(parking_sensor_data):
    if parking_sensor_data['distance'] < 10:
        return "Parking assist: Please stop, obstacle detected"
    return "Parking clear"
