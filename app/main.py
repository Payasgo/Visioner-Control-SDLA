# app/main.py

import time

from app.adas.auto_correction import AutoCorrector
from app.adas.gear_alert import GearAdvisor
from app.adas.speed_control import SpeedController
from app.behavior.classifier import DriverClassifier
from app.behavior.lesson_tracker import LessonTracker
from app.behavior.voice_coach import VoiceCoach
from app.telemetry.simulator_interface import TelemetrySimulator
from app.utils.logger import setup_logger


def start_app(mode: str = "simulator") -> None:
    logger = setup_logger()
    logger.info("Starting Visioner-Control-SDLA in %s mode", mode)

    telemetry = TelemetrySimulator()
    driver_model = DriverClassifier()
    speed_ctrl = SpeedController()
    gear_advisor = GearAdvisor()
    corrector = AutoCorrector()
    tracker = LessonTracker()
    coach = VoiceCoach()

    try:
        while True:
            data = telemetry.get_data()

            # Classify and track *before* logging so the logged values are consistent
            skill = driver_model.classify(data)
            tracker.update(data)

            logger.info(
                "Driver Skill: %s | Speed: %.1f | Gear: %s",
                skill,
                data["speed"],
                data["gear"],
            )

            speed_ctrl.adjust(data["speed"], skill)
            print("[ADAS]", gear_advisor.suggest(data["speed"], data["gear"]))
            corrector.correct(data["steering_angle"], data["lane_offset"])
            coach.give_tip(skill)

            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Simulation stopped by user.")
        logger.info("Lesson summary: %s", tracker.get_summary())
