# Version 0.6.3
# Build 2026-03-10 14:58:29 UTC
from typing import Optional
from modules.moon_visibility.models import VisibilityResult

class DanjonCriterion:
    """
    Simple Danjon-limit check.
    Default working threshold uses 7.0 degrees of elongation / ARCL as a conservative cutoff.
    """

    def __init__(self, limit_deg: float = 7.0) -> None:
        self.limit_deg = limit_deg

    def evaluate(self, arcl_deg: Optional[float]) -> VisibilityResult:
        if arcl_deg is None:
            return VisibilityResult(
                criterion_name="Danjon",
                raw_value=None,
                category="Undetermined",
                explanation="ARCL / elongation is missing.",
                metadata={"limit_deg": self.limit_deg},
            )

        if arcl_deg >= self.limit_deg:
            category = "Above limit"
            explanation = "The elongation is above the configured Danjon threshold."
        else:
            category = "Below limit"
            explanation = "The elongation is below the configured Danjon threshold."

        return VisibilityResult(
            criterion_name="Danjon",
            raw_value=arcl_deg,
            category=category,
            explanation=explanation,
            metadata={"limit_deg": self.limit_deg},
        )
