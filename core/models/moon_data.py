# ============================================================================
# File Name   : moon_data.py
# Title       : Moon Data Model
# Version     : 0.7.5
# Build Date  : 2026-03-11 00:00:00 UTC
# Author      : Dr. Rami Tarawneh
# Company     : 7th Layer
# Project     : Islamic Time System
# Description : Moon data result model.
#               v0.7.5 expands the model so the scientific meaning of each
#               field is easier to audit. New fields explicitly record the
#               conjunction reference, solar altitude at sunset, ARCV, and the
#               sunset-referenced crescent width used by scientific visibility
#               models.
# License     : GNU General Public License v3.0 or later
# ============================================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class MoonData:
    # ---------------------------------------------------------------------
    # Conjunction fields.
    # conjunction:
    #   The resolved new-moon conjunction datetime used by the application.
    # conjunction_reference:
    #   A human-readable label that explains the scientific reference frame.
    #   In v0.7.5 we make this explicit to avoid confusing geocentric
    #   conjunction with topocentric observation metrics.
    # ---------------------------------------------------------------------
    conjunction: datetime | None
    conjunction_reference: str | None

    # ---------------------------------------------------------------------
    # Event times for the evaluated evening.
    # The system treats these as the authoritative event instants for all
    # sunset-based lunar metrics and lag computations.
    # ---------------------------------------------------------------------
    sunset: datetime | None
    moonset: datetime | None

    # ---------------------------------------------------------------------
    # Basic lunar metrics.
    # moon_age_hours:
    #   Age in hours from the resolved geocentric conjunction to the local
    #   sunset being evaluated. This is retained for reporting only and must
    #   not be treated as a standalone visibility decision variable.
    # altitude_deg:
    #   Apparent topocentric lunar altitude at local sunset.
    # solar_altitude_at_sunset_deg:
    #   Apparent topocentric solar altitude at the exact sunset instant used
    #   by the engine. This is preserved to make ARCV traceable.
    # arcv_deg:
    #   Apparent Relative Crescent Vertical distance at sunset, computed as
    #   moon apparent altitude minus sun apparent altitude at the same instant.
    # elongation_deg:
    #   Apparent topocentric sun-moon separation angle at sunset.
    # crescent_width_arcmin:
    #   A sunset-referenced crescent width approximation, expressed in
    #   arcminutes, used by the visibility layer.
    # lag_time_minutes:
    #   Moonset minus sunset using the same rise/set model for both bodies.
    # ---------------------------------------------------------------------
    moon_age_hours: float | None
    altitude_deg: float | None
    solar_altitude_at_sunset_deg: float | None
    arcv_deg: float | None
    elongation_deg: float | None
    crescent_width_arcmin: float | None
    lag_time_minutes: float | None
