# ============================================================================
# File Name   : service.py
# Title       : Moon Service
# Version     : 0.7.5
# Build Date  : 2026-03-11 00:00:00 UTC
# Author      : Dr. Rami Tarawneh
# Company     : 7th Layer
# Project     : Islamic Time System
# Description : Computes moon data and a structured crescent evaluation using a
#               caller-supplied conjunction datetime when available.
#
#               v0.7.5 aligns this service with the new explicit scientific
#               reference model introduced in the astronomy engine. The service
#               now preserves additional sunset-based quantities so later layers
#               do not need to infer them indirectly.
# License     : GNU General Public License v3.0 or later
# ============================================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Optional, Tuple

from core.models.moon_data import MoonData


@dataclass(slots=True)
class CrescentEvaluation:
    astronomical_status: str
    mukth_status: str
    visibility_status: str
    jordan_operational_status: str
    official_status: str
    reason_summary: str
    detailed_reasoning: str


class MoonService:
    def __init__(self, astronomy_engine) -> None:
        self.astronomy_engine = astronomy_engine

    def calculate(
        self,
        location,
        target_date: date,
        conjunction_dt: Optional[datetime] = None,
    ) -> Tuple[MoonData, CrescentEvaluation]:
        # ------------------------------------------------------------------
        # Step 1: resolve the event times that define the evening under study.
        # These are kept as top-level fields because nearly every downstream
        # rule needs them and they also provide traceability when auditing a
        # saved run.
        # ------------------------------------------------------------------
        sunset = self.astronomy_engine.get_sunset(location, target_date)
        moonset = self.astronomy_engine.get_moonset(location, target_date)

        # ------------------------------------------------------------------
        # Step 2: resolve conjunction.
        # The project continues to use the geocentric new moon phase event as
        # the age anchor. We now label this explicitly in the result object so
        # no one mistakes it for a local observer event.
        # ------------------------------------------------------------------
        if conjunction_dt is None:
            conjunction_dt = self.astronomy_engine.get_conjunction(target_date)
        conjunction_reference = (
            "Geocentric astronomical new moon conjunction"
            if conjunction_dt is not None
            else None
        )

        # ------------------------------------------------------------------
        # Step 3: pull all sunset-based observer metrics from the same engine.
        # This is important because it keeps altitude, ARCV, elongation, width,
        # and lag tied to one consistent observer frame and one sunset instant.
        # ------------------------------------------------------------------
        altitude = self.astronomy_engine.get_moon_altitude_at_sunset(location, target_date)
        solar_altitude_at_sunset = self.astronomy_engine.get_solar_altitude_at_sunset(location, target_date)
        arcv = self.astronomy_engine.get_arcv_at_sunset(location, target_date)
        elongation = self.astronomy_engine.get_elongation_at_sunset(location, target_date)
        crescent_width_arcmin = self.astronomy_engine.get_crescent_width_arcmin_at_sunset(location, target_date)
        lag_time = self.astronomy_engine.get_lag_time_minutes(location, target_date)

        # ------------------------------------------------------------------
        # Step 4: compute moon age for reporting.
        # Age is recorded because it remains a standard reporting metric in
        # crescent discussions, but the code and comments now state clearly that
        # it is not, by itself, a sufficient visibility criterion.
        # ------------------------------------------------------------------
        moon_age_hours = None
        if sunset is not None and conjunction_dt is not None:
            conjunction_utc = (
                conjunction_dt.astimezone(timezone.utc)
                if conjunction_dt.tzinfo
                else conjunction_dt.replace(tzinfo=timezone.utc)
            )
            moon_age_hours = (sunset.astimezone(timezone.utc) - conjunction_utc).total_seconds() / 3600.0

        moon_data = MoonData(
            conjunction=conjunction_dt,
            conjunction_reference=conjunction_reference,
            sunset=sunset,
            moonset=moonset,
            moon_age_hours=moon_age_hours,
            altitude_deg=altitude,
            solar_altitude_at_sunset_deg=solar_altitude_at_sunset,
            arcv_deg=arcv,
            elongation_deg=elongation,
            crescent_width_arcmin=crescent_width_arcmin,
            lag_time_minutes=lag_time,
        )
        return moon_data, self._evaluate(moon_data)

    def _evaluate(self, moon_data: MoonData) -> CrescentEvaluation:
        official_status = "Awaiting official decision"

        if moon_data.sunset is None or moon_data.moonset is None:
            return CrescentEvaluation(
                astronomical_status="Incomplete event data",
                mukth_status="Unknown",
                visibility_status="Undetermined",
                jordan_operational_status="Needs review",
                official_status=official_status,
                reason_summary="Sunset or moonset could not be resolved.",
                detailed_reasoning="Verify event calculation inputs and location data.",
            )

        lag = moon_data.lag_time_minutes
        if moon_data.conjunction is None:
            return CrescentEvaluation(
                astronomical_status="Conjunction unresolved",
                mukth_status="Unknown" if lag is None else self._classify_mukth(lag),
                visibility_status="Undetermined",
                jordan_operational_status="Needs review",
                official_status=official_status,
                reason_summary="The conjunction time could not be resolved for the evaluated evening.",
                detailed_reasoning="Provide a resolved conjunction or widen the search window.",
            )

        if lag is None:
            return CrescentEvaluation(
                astronomical_status="Conjunction resolved",
                mukth_status="Unknown",
                visibility_status="Undetermined",
                jordan_operational_status="Needs review",
                official_status=official_status,
                reason_summary="Lag time could not be computed because one of the required event times was missing.",
                detailed_reasoning="Moonset or sunset was missing while conjunction was available.",
            )

        conjunction_local = (
            moon_data.conjunction.astimezone(moon_data.sunset.tzinfo)
            if moon_data.conjunction.tzinfo
            else moon_data.conjunction.replace(tzinfo=timezone.utc).astimezone(moon_data.sunset.tzinfo)
        )

        if conjunction_local > moon_data.sunset:
            return CrescentEvaluation(
                astronomical_status="Conjunction after sunset",
                mukth_status=self._classify_mukth(lag),
                visibility_status="Not visible",
                jordan_operational_status="Next day candidate",
                official_status=official_status,
                reason_summary="The conjunction happens after local sunset.",
                detailed_reasoning="A post-sunset conjunction means the crescent is not yet born for this evening.",
            )

        visibility_status, detailed_reasoning = self._classify_visibility(
            altitude=moon_data.altitude_deg,
            elongation=moon_data.elongation_deg,
            age=moon_data.moon_age_hours,
            lag=lag,
        )

        return CrescentEvaluation(
            astronomical_status="Conjunction before sunset",
            mukth_status=self._classify_mukth(lag),
            visibility_status=visibility_status,
            jordan_operational_status=self._classify_operational_status(visibility_status, lag),
            official_status=official_status,
            reason_summary="The conjunction occurs before sunset and the crescent is evaluated using post-sunset metrics.",
            detailed_reasoning=detailed_reasoning,
        )

    @staticmethod
    def _classify_mukth(lag_minutes: float | None) -> str:
        if lag_minutes is None:
            return "Unknown"
        if lag_minutes <= 0:
            return "No mukth"
        if lag_minutes < 20:
            return "Short mukth"
        if lag_minutes < 40:
            return "Moderate mukth"
        return "Strong mukth"

    @staticmethod
    def _classify_visibility(
        altitude: float | None,
        elongation: float | None,
        age: float | None,
        lag: float | None,
    ) -> tuple[str, str]:
        if altitude is None or elongation is None or age is None or lag is None:
            return (
                "Undetermined",
                "One or more required visibility inputs are missing.",
            )

        if altitude <= 0 or age <= 0 or elongation <= 0:
            return (
                "Not visible",
                "A post-sunset crescent requires positive altitude, positive age after conjunction, and meaningful sun-moon separation.",
            )

        if elongation < 7.0 or lag < 0:
            return (
                "Not visible",
                "The crescent is below the classical lower-visibility geometry or the moon sets before the sun.",
            )

        if altitude >= 10 and lag >= 45 and elongation >= 10:
            return (
                "Likely visible",
                "The crescent has strong post-sunset geometry with healthy altitude, lag, and separation.",
            )

        if altitude >= 5 and lag >= 20 and elongation >= 8:
            return (
                "Marginally visible",
                "The crescent may be visible under good atmospheric conditions and a clear horizon.",
            )

        return (
            "Difficult",
            "The crescent exists geometrically but remains difficult and should be checked against scientific visibility criteria and actual observing conditions.",
        )

    @staticmethod
    def _classify_operational_status(visibility_status: str, lag_minutes: float | None) -> str:
        if visibility_status == "Likely visible":
            return "Same evening candidate"
        if visibility_status == "Marginally visible":
            return "Needs field verification"
        if visibility_status == "Difficult":
            return "High uncertainty"
        if lag_minutes is not None and lag_minutes <= 0:
            return "Next day candidate"
        return "Needs review"
