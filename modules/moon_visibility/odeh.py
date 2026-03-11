# ============================================================================
# File Name   : odeh.py
# Title       : Odeh Visibility Criterion
# Version     : 0.7.5
# Build Date  : 2026-03-11 00:00:00 UTC
# Author      : Dr. Rami Tarawneh
# Company     : 7th Layer
# Project     : Islamic Time System
# Description : Scientific Odeh-style visibility layer using ARCV and crescent
#               width W. v0.7.5 upgrades the interface so callers can provide
#               ARCV and W directly from the astronomy engine instead of forcing
#               the criterion to reconstruct them from rough stand-ins.
# License     : GNU General Public License v3.0 or later
# ============================================================================

from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians
from typing import Optional


@dataclass
class OdehResult:
    arcv_deg: Optional[float]
    w_arcmin: Optional[float]
    v_value: Optional[float]
    zone: str
    explanation: str


class OdehCriterion:
    """
    Odeh-style crescent visibility evaluation.

    Scientific note for v0.7.5:
    - Preferred inputs are ARCV and crescent width W already computed from the
      astronomy engine at the exact sunset instant under an apparent,
      topocentric frame.
    - Fallbacks based on altitude and elongation are preserved for defensive
      compatibility only.
    """

    SOLAR_APPARENT_ALTITUDE_AT_SUNSET = -0.833
    NOMINAL_LUNAR_DIAMETER_ARCMIN = 31.0

    def evaluate(
        self,
        altitude_deg: Optional[float] = None,
        elongation_deg: Optional[float] = None,
        arcv_deg: Optional[float] = None,
        w_arcmin: Optional[float] = None,
    ) -> OdehResult:
        # ------------------------------------------------------------------
        # Resolve ARCV.
        # Preferred path: accept a direct astronomy-engine ARCV value.
        # Fallback path: reconstruct from altitude using the traditional
        # standard solar altitude at sunset. The fallback remains here only to
        # avoid breaking old callers while the project migrates.
        # ------------------------------------------------------------------
        if arcv_deg is None and altitude_deg is not None:
            arcv_deg = altitude_deg - self.SOLAR_APPARENT_ALTITUDE_AT_SUNSET

        # ------------------------------------------------------------------
        # Resolve crescent width W.
        # Preferred path: use a pre-computed width from the engine.
        # Fallback path: estimate illuminated fraction from elongation and a
        # nominal lunar diameter. This is still an approximation, but better
        # than using elongation itself as a surrogate width.
        # ------------------------------------------------------------------
        if w_arcmin is None and elongation_deg is not None:
            illuminated_fraction = (1.0 - cos(radians(elongation_deg))) / 2.0
            w_arcmin = self.NOMINAL_LUNAR_DIAMETER_ARCMIN * illuminated_fraction

        if arcv_deg is None or w_arcmin is None:
            return OdehResult(
                arcv_deg=arcv_deg,
                w_arcmin=w_arcmin,
                v_value=None,
                zone="Undetermined",
                explanation="ARCV or crescent width W is missing, so the Odeh visibility result cannot be computed.",
            )

        threshold = (
            -0.1018 * (w_arcmin ** 3)
            + 0.7319 * (w_arcmin ** 2)
            - 6.3226 * w_arcmin
            + 7.1651
        )
        v_value = arcv_deg - threshold

        if v_value >= 5.65:
            zone = "A"
            explanation = "Visible by naked eye."
        elif v_value >= 2.0:
            zone = "B"
            explanation = "Visible by naked eye under perfect atmospheric conditions."
        elif v_value >= -0.96:
            zone = "C"
            explanation = "Visible by optical aid; naked-eye sighting may be possible for an experienced observer under excellent conditions."
        else:
            zone = "D"
            explanation = "Not visible, even with optical aid."

        return OdehResult(
            arcv_deg=arcv_deg,
            w_arcmin=w_arcmin,
            v_value=v_value,
            zone=zone,
            explanation=explanation,
        )
