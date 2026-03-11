# ============================================================================
# File Name   : conjunction_service.py
# Title       : Next Conjunction Service
# Version     : 0.3.2
# Build Date  : 2026-03-09 17:22:01 UTC
# Author      : Dr. Rami Tarawneh
# Company     : 7th Layer
# Project     : Islamic Time System
# Description : Finds the first new moon conjunction on or after a supplied
#               Gregorian date using Skyfield moon phases.
# License     : GNU General Public License v3.0 or later
# ============================================================================

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Optional

from skyfield import almanac

class ConjunctionService:
    def __init__(self, astronomy_engine) -> None:
        self.astronomy_engine = astronomy_engine
        self.ts = astronomy_engine.ts
        self.eph = astronomy_engine.eph

    def find_next_conjunction(self, start_date: date) -> Optional[datetime]:
        start_dt = datetime.combine(start_date, time(0, 0, 0), tzinfo=timezone.utc)
        end_dt = start_dt + timedelta(days=40)
        t0 = self.ts.from_datetime(start_dt)
        t1 = self.ts.from_datetime(end_dt)
        moon_phases = almanac.moon_phases(self.eph)
        times, phases = almanac.find_discrete(t0, t1, moon_phases)
        for t, phase in zip(times, phases):
            if int(phase) == 0:
                return t.utc_datetime().replace(tzinfo=timezone.utc)
        return None
