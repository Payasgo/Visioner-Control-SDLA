# app/main.py

from app.adas.speed_control import SpeedController
from app.adas.gear_alert import GearAdvisor
from app.adas.auto_correction import AutoCorrector
from app.behavior.classifier import DriverClassifier
from app.telemetry.simulator_interface import TelemetrySimulator
from app.utils.logger import setup_logger

def start_app(mode="simulator"):
    logger = setup_logger()

    logger.info("Starting Visioner-Control-SDLA in %s mode", mode)

    telemetry = TelemetrySimulator()
    driver_model = DriverClassifier()
    speed_ctrl = SpeedController()
    gear_advisor = GearAdvisor()
    corrector = AutoCorrector()

    try:
        while True:
            data = telemetry.get_data()
            skill = driver_model.classify(data)

            logger.info(f"Driver Skill: {skill} | Speed: {data['speed']} | Gear: {data['gear']}")

            # ADAS modules
            speed_ctrl.adjust(data["speed"], skill)
            print("[ADAS]", gear_advisor.suggest(data["speed"], data["gear"]))
            corrector.correct(data["steering_angle"], data["lane_offset"])

    except KeyboardInterrupt:
        logger.info("Simulation stopped by user.")
