# scripts/vision_pipeline.py
"""
Full computer-vision pipeline for Visioner-Control-SDLA.

Wires together every new detector:
  • Vehicle Detection + Tracking  (features 1, 2)
  • Lane Detection + Departure    (features 4, 5)
  • ANPR / OCR                    (features 6, 7)
  • Helmet, Seatbelt, Phone       (features 8, 9, 10)
  • Distraction Detection         (feature 12)
  • Drunk Driver Detection        (feature 13)
  • Honk Detection                (feature 14 – audio thread)
  • Traffic Light Detection       (feature 15)
  • Traffic Sign Recognition      (feature 16)
  • Collision Warning             (feature 17)
  • Pedestrian Detection          (feature 18)
  • Obstacle Detection            (feature 19)
  • Blind Spot Detection          (feature 20)
  • Parking Assistance            (feature 21)
  • Evidence Capture              (feature 25)
  • Violation Logging             (feature 26)

Run:
    python -m scripts.vision_pipeline
    python -m scripts.vision_pipeline --source path/to/video.mp4
    python -m scripts.vision_pipeline --parking   # parking-assist mode
"""

from __future__ import annotations

import argparse
import sys
import os
import time
import threading
from datetime import datetime

import cv2
import numpy as np

# Ensure project root on path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ── New modules ──────────────────────────────────────────────────────────────
from app.vision.vehicle_tracker  import VehicleTracker
from app.vision.lane_detector    import LaneDetector
from app.vision.anpr             import ANPRProcessor
from app.vision.safety_detectors import (
    HelmetDetector, SeatbeltDetector,
    PhoneUsageDetector, DistractionDetector,
    DrunkDriverDetector, HonkDetector, HonkEvent,
)
from app.vision.road_scene import (
    TrafficLightDetector, TrafficSignRecognizer,
    CollisionWarning, PedestrianDetector,
    ObstacleDetector, BlindSpotDetector, ParkingAssistant,
)
from app.enforcement.evidence import EvidenceCapture, ViolationLogger

# ── Existing modules ─────────────────────────────────────────────────────────
from scripts.skill_scorer    import SkillScorer
from scripts.coaching_engine import coaching_advice, speak


def _parse_args():
    p = argparse.ArgumentParser(description="Visioner-Control Full CV Pipeline")
    p.add_argument("--source",  default="0",
                   help="Camera index or video file path")
    p.add_argument("--parking", action="store_true",
                   help="Enable parking-assist overlay mode")
    p.add_argument("--no-display", action="store_true",
                   help="Headless mode (no cv2.imshow)")
    p.add_argument("--evidence-dir", default="data/evidence")
    p.add_argument("--log-dir",      default="data/logs")
    return p.parse_args()


def main() -> None:
    args   = _parse_args()
    source = int(args.source) if args.source.isdigit() else args.source

    # ── Infrastructure ───────────────────────────────────────────────
    evidence = EvidenceCapture(args.evidence_dir)
    vlogger  = ViolationLogger(args.log_dir)
    scorer   = SkillScorer()

    # Shared callback: log + score any violation
    def on_violation(vtype: str, plate: str = "UNKNOWN",
                     speed: float | None = None, frame=None, bbox=None):
        ev_path = ""
        if frame is not None:
            ev_path = evidence.capture(frame, vtype, plate,
                                       timestamp=datetime.now(), roi_bbox=bbox)
        vlogger.log(vtype, plate, speed, evidence_path=ev_path)
        speak(f"Warning: {vtype.replace('_', ' ').lower()} detected.")

    # ── Detectors ────────────────────────────────────────────────────
    tracker       = VehicleTracker()
    lane_det      = LaneDetector()
    anpr          = ANPRProcessor()
    helmet_det    = HelmetDetector()
    seatbelt_det  = SeatbeltDetector()
    phone_det     = PhoneUsageDetector()
    distract_det  = DistractionDetector()
    drunk_det     = DrunkDriverDetector()
    tl_det        = TrafficLightDetector()
    sign_det      = TrafficSignRecognizer()
    collision     = CollisionWarning()
    ped_det       = PedestrianDetector()
    obstacle_det  = ObstacleDetector()
    blind_det     = BlindSpotDetector()
    parking       = ParkingAssistant()

    # ── Honk detector (audio thread) ─────────────────────────────────
    def _on_honk(event: HonkEvent):
        print(f"[HONK] energy={event.energy:.0f}")
        vlogger.log("HONKING", "AUDIO_ONLY")
        speak("Unnecessary honking detected.")

    honk_det = HonkDetector(on_honk=_on_honk)
    honk_det.start()

    # ── Video capture ────────────────────────────────────────────────
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open source: {source}")
        sys.exit(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    print(f"[INFO] Pipeline running. FPS={fps}. Press Q to quit.")

    frame_n = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.05)
                continue
            frame_n += 1
            ts = datetime.now()

            # ── 1 & 2: Vehicle detection + tracking ──────────────────
            tracked = tracker.update(frame)

            if args.parking:
                # Parking mode: skip full pipeline
                parking.process(frame)
            else:
                # ── 4 & 5: Lane detection + departure ────────────────
                frame, departures = lane_det.process(frame, tracked)
                for dep in departures:
                    on_violation("LANE_DEPARTURE", frame=frame)

                # ── 6 & 7: ANPR / OCR on each vehicle bbox ───────────
                plates: dict[int, str] = {}
                for tid, info in tracked.items():
                    x1, y1, x2, y2 = info["bbox"]
                    result = anpr.process_frame(frame, (x1, y1, x2-x1, y2-y1))
                    plates[tid] = result.text if result else "UNKNOWN"

                # ── 8: Helmet ─────────────────────────────────────────
                for hr in helmet_det.process(frame, tracked):
                    if not hr.has_helmet:
                        on_violation("NO_HELMET", plates.get(hr.track_id, "UNKNOWN"),
                                     frame=frame, bbox=tracked[hr.track_id]["bbox"])

                # ── 9: Seatbelt ───────────────────────────────────────
                for sr in seatbelt_det.process(frame, tracked):
                    if not sr.has_seatbelt and sr.track_id in seatbelt_det._alerted:
                        on_violation("NO_SEATBELT", plates.get(sr.track_id, "UNKNOWN"),
                                     frame=frame, bbox=tracked[sr.track_id]["bbox"])

                # ── 10: Phone usage ───────────────────────────────────
                for pr in phone_det.process(frame, tracked):
                    if pr.phone_detected and pr.track_id in phone_det._alerted:
                        on_violation("PHONE_USAGE", plates.get(pr.track_id, "UNKNOWN"),
                                     frame=frame, bbox=tracked[pr.track_id]["bbox"])

                # ── 12: Distraction ───────────────────────────────────
                for dr in distract_det.process(frame, tracked):
                    if dr.distracted and dr.track_id in distract_det._alerted:
                        on_violation("DISTRACTION", plates.get(dr.track_id, "UNKNOWN"),
                                     frame=frame, bbox=tracked[dr.track_id]["bbox"])

                # ── 13: Drunk driver ──────────────────────────────────
                for ddr in drunk_det.process(frame, tracked):
                    if ddr.flagged:
                        on_violation(f"DRUNK_{ddr.reason}",
                                     plates.get(ddr.track_id, "UNKNOWN"),
                                     frame=frame, bbox=tracked[ddr.track_id]["bbox"])

                # ── 15: Traffic light ─────────────────────────────────
                tl = tl_det.process(frame, tracked)
                if tl.red_light_violation:
                    on_violation("RED_LIGHT", frame=frame)

                # ── 16: Traffic sign ──────────────────────────────────
                sign_det.process(frame)

                # ── 17: Collision warning ─────────────────────────────
                for ca in collision.process(frame, tracked):
                    on_violation("COLLISION_WARNING",
                                 plates.get(ca.track_id, "UNKNOWN"), frame=frame)

                # ── 18: Pedestrian ────────────────────────────────────
                ped_det.process(frame, tracked)

                # ── 19: Obstacle ──────────────────────────────────────
                obstacle_det.process(frame, tracked)

                # ── 20: Blind spot ────────────────────────────────────
                for bsa in blind_det.process(frame, tracked):
                    speak(f"Vehicle in your {bsa.side.lower()} blind spot.")

                # ── Existing coaching from OBD/sim data ──────────────
                # (kept separate so we don't need a second telemetry call here)

            # ── HUD ───────────────────────────────────────────────────
            h, w = frame.shape[:2]
            ov = frame.copy()
            cv2.rectangle(ov, (0, 0), (w, 38), (0, 0, 0), -1)
            cv2.addWeighted(ov, 0.5, frame, 0.5, 0, frame)
            cv2.putText(frame,
                        f"Visioner-SDLA | {ts.strftime('%H:%M:%S')} "
                        f"| Vehicles: {len(tracked)} | Frame: {frame_n}",
                        (8, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0,255,0), 1)

            if not args.no_display:
                cv2.imshow("Visioner-Control SDLA", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user.")
    finally:
        honk_det.stop()
        cap.release()
        cv2.destroyAllWindows()
        print(f"[INFO] Evidence saved: {evidence.count} images → {args.evidence_dir}")
        print(f"[INFO] Violations logged → {vlogger.csv_path}")


if __name__ == "__main__":
    main()
