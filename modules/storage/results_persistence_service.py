# ============================================================================
# File Name   : results_persistence_service.py
# Title       : Results Persistence Service
# Version     : 0.5.2
# Build Date  : 2026-03-09 21:22:25 UTC
# Author      : Dr. Rami Tarawneh
# Company     : 7th Layer
# Project     : Islamic Time System
# Description : Saves prayer times, moon data, scientific visibility results,
#               and operational evaluation results to MySQL using the existing
#               results tables.
# License     : GNU General Public License v3.0 or later
# ============================================================================

from __future__ import annotations

from datetime import date
from typing import Any

from results_repository import ResultsRepository


class ResultsPersistenceService:
    def __init__(self) -> None:
        self.repo = ResultsRepository()

    def save_all(
        self,
        location,
        gregorian_date: date,
        prayer_times,
        moon_data,
        odeh_result,
        crescent_eval,
    ) -> int:
        run_id = self.repo.create_run(
            city=location.name,
            lat=location.latitude,
            lon=location.longitude,
            gdate=gregorian_date.isoformat(),
        )

        self.repo.insert_prayer_times(
            run_id,
            {
                "fajr": self._to_mysql_datetime(prayer_times.fajr),
                "sunrise": self._to_mysql_datetime(prayer_times.sunrise),
                "dhuhr": self._to_mysql_datetime(prayer_times.dhuhr),
                "asr": self._to_mysql_datetime(prayer_times.asr),
                "maghrib": self._to_mysql_datetime(prayer_times.maghrib),
                "isha": self._to_mysql_datetime(prayer_times.isha),
            },
        )

        self.repo.insert_moon_data(
            run_id,
            {
                "age": moon_data.moon_age_hours,
                "altitude": moon_data.altitude_deg,
                "elongation": moon_data.elongation_deg,
                "lag": moon_data.lag_time_minutes,
            },
        )

        self.repo.insert_visibility(
            run_id,
            {
                "criterion": "Odeh",
                "value": odeh_result.v_value,
                "category": odeh_result.zone,
                "explanation": odeh_result.explanation,
            },
        )

        self.repo.insert_visibility(
            run_id,
            {
                "criterion": "JordanOperational",
                "value": None,
                "category": crescent_eval.jordan_operational_status,
                "explanation": crescent_eval.reason_summary,
            },
        )

        return run_id

    @staticmethod
    def _to_mysql_datetime(value: Any):
        if value is None:
            return None
        try:
            return value.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return value
