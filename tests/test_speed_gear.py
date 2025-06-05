from modules.speed_gear import check_speed_limit, gear_alert

def test_check_speed_limit_city():
    assert check_speed_limit(60) == "Speed limit exceeded! Limit is 50 km/h"
    assert check_speed_limit(45) is None

def test_check_speed_limit_highway():
    assert check_speed_limit(100, city_traffic=False) == "Speed limit exceeded! Limit is 90 km/h"

def test_gear_alert_up():
    assert gear_alert(1, 40) == "Consider shifting up"

def test_gear_alert_down():
    assert gear_alert(4, 10) == "Consider shifting down"
