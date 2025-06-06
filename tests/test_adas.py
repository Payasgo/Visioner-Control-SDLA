# tests/test_adas.py

import pytest
from app.adas.speed_control import SpeedController
from app.adas.gear_alert import GearAdvisor
from app.adas.auto_correction import AutoCorrector

def test_speed_controller_warns_beginner(capsys):
    sc = SpeedController()
    sc.adjust(50, "Beginner")
    captured = capsys.readouterr()
    assert "Reduce speed" in captured.out

def test_gear_advisor_low_speed():
    advisor = GearAdvisor()
    message = advisor.suggest(speed=10, gear=3)
    assert "Downshift" in message

def test_auto_correction_left(capsys):
    corrector = AutoCorrector()
    corrector.correct(-10, 0.7)
    captured = capsys.readouterr()
    assert "Left deviation" in captured.out
