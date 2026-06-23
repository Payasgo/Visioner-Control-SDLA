# scripts/skill_scorer.py


class SkillScorer:
    """
    Maintains a running score for a single driving session.

    Using a class eliminates the mutable global that caused state to leak
    across sessions when the module was imported more than once.
    """

    INITIAL_SCORE: int = 100
    DROWSY_PENALTY: int = 5
    SPEED_PENALTY: int = 3
    BRAKE_PENALTY: int = 1
    SPEED_THRESHOLD: float = 70.0

    def __init__(self) -> None:
        self.score: int = self.INITIAL_SCORE

    def update(self, driver_state: str, vehicle_data: dict) -> int:
        """Apply penalties and return the current score (minimum 0)."""
        if driver_state == "Drowsy":
            self.score -= self.DROWSY_PENALTY
        if vehicle_data.get("speed", 0) > self.SPEED_THRESHOLD:
            self.score -= self.SPEED_PENALTY
        if vehicle_data.get("brake", False):
            self.score -= self.BRAKE_PENALTY
        self.score = max(self.score, 0)
        return self.score

    def reset(self) -> None:
        self.score = self.INITIAL_SCORE
