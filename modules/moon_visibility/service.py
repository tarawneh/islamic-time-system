# ============================================================================
# File Name   : service.py
# Title       : Moon Visibility Service
# Version     : 0.7.5
# Build Date  : 2026-03-11 00:00:00 UTC
# Author      : Dr. Rami Tarawneh
# Company     : 7th Layer
# Project     : Islamic Time System
# Description : Wrapper service for the scientific visibility layer.
#               v0.7.5 now feeds Odeh and Yallop with explicit sunset-based
#               ARCV and crescent-width inputs when available, keeping the
#               visibility layer aligned with the corrected astronomy engine.
# License     : GNU General Public License v3.0 or later
# ============================================================================

from modules.moon_visibility.models import VisibilityResult
from modules.moon_visibility.odeh import OdehCriterion
from modules.moon_visibility.yallop import YallopCriterion
from modules.moon_visibility.danjon import DanjonCriterion


class MoonVisibilityService:
    def __init__(self):
        self.odeh = OdehCriterion()
        self.yallop = YallopCriterion()
        self.danjon = DanjonCriterion()

    def evaluate(self, moon_data):
        return self.odeh.evaluate(
            altitude_deg=moon_data.altitude_deg,
            elongation_deg=moon_data.elongation_deg,
            arcv_deg=moon_data.arcv_deg,
            w_arcmin=moon_data.crescent_width_arcmin,
        )

    def evaluate_all(self, moon_data):
        odeh_raw = self.odeh.evaluate(
            altitude_deg=moon_data.altitude_deg,
            elongation_deg=moon_data.elongation_deg,
            arcv_deg=moon_data.arcv_deg,
            w_arcmin=moon_data.crescent_width_arcmin,
        )

        odeh_result = VisibilityResult(
            criterion_name="Odeh",
            raw_value=getattr(odeh_raw, "v_value", None),
            category=getattr(odeh_raw, "zone", "Unknown"),
            explanation=getattr(odeh_raw, "explanation", ""),
            metadata={
                "arcv_deg": getattr(odeh_raw, "arcv_deg", None),
                "w_arcmin": getattr(odeh_raw, "w_arcmin", None),
                "solar_altitude_at_sunset_deg": getattr(moon_data, "solar_altitude_at_sunset_deg", None),
            },
        )

        arcv = getattr(odeh_raw, "arcv_deg", None)
        w_arcmin = getattr(odeh_raw, "w_arcmin", None)
        arcl = moon_data.elongation_deg

        yallop_result = self.yallop.evaluate(
            arcv_deg=arcv,
            w_arcmin=w_arcmin,
            arcl_deg=arcl,
        )

        danjon_result = self.danjon.evaluate(arcl_deg=arcl)

        return [
            odeh_result,
            yallop_result,
            danjon_result,
        ]
