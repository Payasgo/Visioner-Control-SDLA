# app/adas/auto_correction.py

class AutoCorrector:
    def correct(self, steering_angle, lane_offset):
        if abs(lane_offset) > 0.5:
            print(f"[ADAS] Auto-correcting: Adjusting steering by {-lane_offset * 0.3:.2f}°")
        else:
            print("[ADAS] Lane position stable.")
