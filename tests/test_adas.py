# tests/test_adas.py

from app.adas.auto_correction import AutoCorrector
from app.adas.gear_alert import GearAdvisor
from app.adas.speed_control import SpeedController


# ── SpeedController ──────────────────────────────────────────────────────────

def test_speed_controller_warns_beginner(capsys):
    sc = SpeedController()
    sc.adjust(50, "Beginner")
    captured = capsys.readouterr()
    assert "Reduce speed" in captured.out


def test_speed_controller_warns_medium(capsys):
    sc = SpeedController()
    sc.adjust(70, "Medium")
    captured = capsys.readouterr()
    assert "Reduce speed" in captured.out


def test_speed_controller_warns_pro(capsys):
    sc = SpeedController()
    sc.adjust(90, "Pro")
    captured = capsys.readouterr()
    assert "Reduce speed" in captured.out


def test_speed_controller_no_warning_within_limit(capsys):
    sc = SpeedController()
    result = sc.adjust(30, "Beginner")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert result is None


def test_speed_controller_unknown_skill_no_crash():
    sc = SpeedController()
    result = sc.adjust(200, "Alien")
    assert result is None


# ── GearAdvisor ──────────────────────────────────────────────────────────────

def test_gear_advisor_low_speed():
    advisor = GearAdvisor()
    message = advisor.suggest(speed=10, gear=3)
    assert "Downshift" in message


def test_gear_advisor_high_speed_low_gear():
    advisor = GearAdvisor()
    message = advisor.suggest(speed=50, gear=2)
    assert "higher gear" in message


def test_gear_advisor_appropriate():
    advisor = GearAdvisor()
    message = advisor.suggest(speed=40, gear=3)
    assert "appropriate" in message


# ── AutoCorrector ─────────────────────────────────────────────────────────────

def test_auto_correction_right(capsys):
    corrector = AutoCorrector()
    result = corrector.correct(-10, 0.7)   # positive offset → right drift
    captured = capsys.readouterr()
    assert "Right deviation" in captured.out
    assert result is not None


def test_auto_correction_left(capsys):
    corrector = AutoCorrector()
    result = corrector.correct(-10, -0.7)  # negative offset → left drift
    captured = capsys.readouterr()
    assert "Left deviation" in captured.out
    assert result is not None


def test_auto_correction_stable(capsys):
    corrector = AutoCorrector()
    result = corrector.correct(0, 0.2)
    captured = capsys.readouterr()
    assert "stable" in captured.out
    assert result is None
