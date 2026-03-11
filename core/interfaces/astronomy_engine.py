# ============================================================================
# File Name   : astronomy_engine.py
# Title       : Astronomy Engine Interface
# Version     : 0.7.5
# Build Date  : 2026-03-11 00:00:00 UTC
# Author      : Dr. Rami Tarawneh
# Company     : 7th Layer
# Project     : Islamic Time System
# Description : Protocol for astronomy engine implementations.
#               This interface was expanded in v0.7.5 to make the scientific
#               reference frame explicit. The new methods let downstream
#               services request apparent, topocentric, sunset-referenced lunar
#               metrics instead of rebuilding them independently.
# License     : GNU General Public License v3.0 or later
# ============================================================================

from __future__ import annotations

from datetime import date, datetime
from typing import Protocol

from core.models.location import Location


class AstronomyEngine(Protocol):
    # ---------------------------------------------------------------------
    # Core rise/set events.
    # These methods are expected to use one internally consistent event
    # definition so that sunset, moonset, altitude, and lag time all refer
    # to the same observational model.
    # ---------------------------------------------------------------------
    def get_sunrise(self, location: Location, target_date: date) -> datetime | None: ...
    def get_sunset(self, location: Location, target_date: date) -> datetime | None: ...
    def get_moonrise(self, location: Location, target_date: date) -> datetime | None: ...
    def get_moonset(self, location: Location, target_date: date) -> datetime | None: ...
    def get_solar_noon(self, location: Location, target_date: date) -> datetime | None: ...

    # ---------------------------------------------------------------------
    # Conjunction.
    # The current project definition keeps conjunction geocentric because the
    # new moon phase event itself is an Earth-Moon-Sun geometry event, while
    # observation metrics remain topocentric.
    # ---------------------------------------------------------------------
    def get_conjunction(self, target_date: date) -> datetime | None: ...

    # ---------------------------------------------------------------------
    # Sunset-referenced lunar observation metrics.
    # Each value below should be computed at the same local sunset instant and
    # from the same apparent, topocentric observer frame unless otherwise
    # documented.
    # ---------------------------------------------------------------------
    def get_moon_altitude_at_sunset(self, location: Location, target_date: date) -> float | None: ...
    def get_solar_altitude_at_sunset(self, location: Location, target_date: date) -> float | None: ...
    def get_arcv_at_sunset(self, location: Location, target_date: date) -> float | None: ...
    def get_elongation_at_sunset(self, location: Location, target_date: date) -> float | None: ...
    def get_crescent_width_arcmin_at_sunset(self, location: Location, target_date: date) -> float | None: ...
    def get_lag_time_minutes(self, location: Location, target_date: date) -> float | None: ...
