# app/adas/auto_correction.py


class AutoCorrector:
    """Detects lane deviation and computes a steering correction."""

    DEVIATION_THRESHOLD: float = 0.5
    CORRECTION_GAIN: float = 0.3

    def correct(self, steering_angle: float, lane_offset: float) -> str | None:
        """
        Returns a correction message when |lane_offset| exceeds the threshold,
        otherwise returns None (stable).

        Args:
            steering_angle: Current steering angle in degrees (unused here but
                            available for future closed-loop control).
            lane_offset:    Lateral offset from lane centre in metres; positive
                            means drifting right, negative means drifting left.
        """
        if abs(lane_offset) > self.DEVIATION_THRESHOLD:
            # lane_offset > 0 → drifting right → correct left, and vice-versa
            direction = "Right" if lane_offset > 0 else "Left"
            correction = -lane_offset * self.CORRECTION_GAIN
            msg = (
                f"[ADAS] {direction} deviation detected. "
                f"Auto-correcting by {correction:.2f} deg."
            )
            print(msg)
            return msg

        print("[ADAS] Lane position stable.")
        return None
