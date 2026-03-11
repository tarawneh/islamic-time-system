# ============================================================================
# File Name   : crescent_candidate_service.py
# Title       : Crescent Candidate Service
# Version     : 0.3.2
# Build Date  : 2026-03-09 17:22:01 UTC
# Author      : Dr. Rami Tarawneh
# Company     : 7th Layer
# Project     : Islamic Time System
# Description : Determines the first local evening to evaluate after a resolved
#               new moon conjunction.
# License     : GNU General Public License v3.0 or later
# ============================================================================

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional, Tuple

class CrescentCandidateService:
    def __init__(self, astronomy_engine) -> None:
        self.astronomy_engine = astronomy_engine

    def find_candidate_evening(self, location, conjunction_dt: datetime | None) -> Tuple[date, str]:
        if conjunction_dt is None:
            fallback = date.today()
            return fallback, "No conjunction was resolved. The returned candidate evening is a placeholder and needs review."

        local_conjunction = conjunction_dt.astimezone(timezone.utc).astimezone(
            __import__("zoneinfo").ZoneInfo(location.timezone)
        )
        conjunction_date = local_conjunction.date()
        sunset = self.astronomy_engine.get_sunset(location, conjunction_date)

        if sunset is None:
            return (
                conjunction_date + timedelta(days=1),
                "Sunset on the conjunction date could not be resolved, so the next evening was selected conservatively.",
            )

        if local_conjunction <= sunset:
            return (
                conjunction_date,
                "The conjunction occurs before local sunset, so the same evening is the first candidate for crescent evaluation.",
            )

        return (
            conjunction_date + timedelta(days=1),
            "The conjunction occurs after local sunset, so the next evening is the first candidate for crescent evaluation.",
        )
