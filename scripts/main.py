# scripts/main.py
#
# Run from the project root:
#   python -m scripts.main
# or add the project root to PYTHONPATH:
#   PYTHONPATH=. python scripts/main.py

import sys
import os

# Ensure project root is on the path when executed directly
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import cv2

from scripts.driver_monitor import get_driver_state
from scripts.obd_simulator import get_vehicle_data
from scripts.coaching_engine import coaching_advice
from scripts.skill_scorer import SkillScorer


def main() -> None:
    scorer = SkillScorer()
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("[ERROR] Could not open camera. Exiting.")
        sys.exit(1)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[WARN] Failed to capture frame; skipping.")
                continue

            driver_state = get_driver_state(frame)
            vehicle_data = get_vehicle_data()

            coaching_advice(driver_state, vehicle_data)
            score = scorer.update(driver_state, vehicle_data)

            cv2.putText(
                frame,
                f"State: {driver_state}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )
            cv2.putText(
                frame,
                f"Speed: {vehicle_data['speed']:.0f} km/h",
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 0, 0),
                2,
            )
            cv2.putText(
                frame,
                f"Score: {score}",
                (10, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2,
            )

            cv2.imshow("Visioner Control SDLA", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
