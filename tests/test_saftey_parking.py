from modules.safety_parking import auto_correct, parking_logic

def test_auto_correct_within_threshold():
    assert auto_correct(10) == 10

def test_auto_correct_exceeds_threshold():
    assert auto_correct(30) == 15.0  # 30 * 0.5

def test_parking_logic_clear():
    assert parking_logic({'distance': 20}) == "Parking clear"

def test_parking_logic_obstacle():
    assert parking_logic({'distance': 5}) == "Parking assist: Please stop, obstacle detected"
