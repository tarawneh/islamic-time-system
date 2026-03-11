# Version 0.6.3
# Build 2026-03-10 14:58:29 UTC
from dataclasses import dataclass
from typing import Optional
from modules.moon_visibility.models import VisibilityResult

class YallopCriterion:
    """
    q = (ARCV - (11.871 - 6.3226*W + 0.7319*W^2 - 0.1018*W^3)) / 10

    Categories:
    A: q > 0.216
    B: 0.216 >= q > -0.014
    C: -0.014 >= q > -0.160
    D: -0.160 >= q > -0.232
    E: -0.232 >= q > -0.293
    F: q <= -0.293
    """

    def evaluate(self, arcv_deg: Optional[float], w_arcmin: Optional[float], arcl_deg: Optional[float] = None) -> VisibilityResult:
        if arcv_deg is None or w_arcmin is None:
            return VisibilityResult(
                criterion_name="Yallop",
                raw_value=None,
                category="Undetermined",
                explanation="ARCV or crescent width W is missing.",
                metadata={"arcv_deg": arcv_deg, "w_arcmin": w_arcmin, "arcl_deg": arcl_deg},
            )

        q = (arcv_deg - (11.871 - 6.3226 * w_arcmin + 0.7319 * (w_arcmin ** 2) - 0.1018 * (w_arcmin ** 3))) / 10.0

        if q > 0.216:
            category = "A"
            explanation = "Easily visible."
        elif q > -0.014:
            category = "B"
            explanation = "Visible under perfect conditions."
        elif q > -0.160:
            category = "C"
            explanation = "May need optical aid to find crescent."
        elif q > -0.232:
            category = "D"
            explanation = "Will need optical aid to find crescent."
        elif q > -0.293:
            category = "E"
            explanation = "Not visible with a telescope."
        else:
            category = "F"
            explanation = "Not visible; below the Danjon limit or too weak for visibility."

        if arcl_deg is not None and arcl_deg <= 8.0:
            explanation += " ARCL is at or below the classical lower-visibility region."

        return VisibilityResult(
            criterion_name="Yallop",
            raw_value=q,
            category=category,
            explanation=explanation,
            metadata={"arcv_deg": arcv_deg, "w_arcmin": w_arcmin, "arcl_deg": arcl_deg},
        )
