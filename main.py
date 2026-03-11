# ============================================================================
# File Name   : main.py
# Title       : Islamic Time System CLI
# Version     : 0.5.2
# Build Date  : 2026-03-09 21:22:25 UTC
# Author      : Dr. Rami Tarawneh
# Company     : 7th Layer
# Project     : Islamic Time System
# Description : Full-file replacement for the CLI entry point. This version
#               keeps the current calculation flow and adds automatic result
#               persistence to MySQL after each successful calculation.
# License     : GNU General Public License v3.0 or later
# ============================================================================

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from core.models.location import Location
from modules.astronomy.basic_engine import BasicAstronomyEngine
from modules.hijri.conjunction_service import ConjunctionService
from modules.hijri.crescent_candidate_service import CrescentCandidateService
from modules.hijri.estimation_service import HijriEstimationService
from modules.moon.service import MoonService
from modules.moon_visibility.service import MoonVisibilityService
from modules.prayer_times.service import PrayerTimeService
from modules.storage.results_persistence_service import ResultsPersistenceService


def parse_args():
    parser = argparse.ArgumentParser(description="Islamic Time System CLI")
    parser.add_argument("--city", required=True, help="City name, for example: Amman")
    parser.add_argument("--date", required=True, help="Gregorian date in YYYY-MM-DD format")
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Calculate normally but skip saving results to MySQL",
    )
    return parser.parse_args()


def load_location(city_name: str) -> Location:
    data_file = Path("data") / "jordan_cities.json"
    payload = json.loads(data_file.read_text(encoding="utf-8"))
    for item in payload:
        if item["name"].strip().lower() == city_name.strip().lower():
            return Location(
                name=item["name"],
                latitude=item["latitude"],
                longitude=item["longitude"],
                elevation_meters=item["elevation"],
                timezone=item["timezone"],
            )
    raise ValueError(f"City not found: {city_name}")


def fmt_dt(value):
    if value is None:
        return "N/A"
    return value.strftime("%Y-%m-%d %H:%M:%S %z")


def fmt_float(value, digits=2, suffix=""):
    if value is None:
        return "N/A"
    return f"{value:.{digits}f}{suffix}"


def fmt_lag(value):
    if value is None:
        return "N/A"
    if value <= 0:
        return "Not applicable"
    return f"{value:.2f} min"


def fmt_q(value):
    if value is None:
        return "N/A"
    return f"{value:.4f}"


def format_estimated_hijri(value):
    if value is None:
        return "N/A"
    try:
        return f"{value.day} {value.month_name} {value.year} ({value.source})"
    except Exception:
        return str(value)


def main():
    args = parse_args()
    target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    location = load_location(args.city)

    astronomy_engine = BasicAstronomyEngine()
    prayer_service = PrayerTimeService(astronomy_engine)
    moon_service = MoonService(astronomy_engine)
    visibility_service = MoonVisibilityService()

    hijri_service = HijriEstimationService()
    conjunction_service = ConjunctionService(astronomy_engine)
    candidate_service = CrescentCandidateService(astronomy_engine)

    prayer_times = prayer_service.calculate(location, target_date)

    estimated_hijri = hijri_service.estimate(target_date)
    next_conjunction = conjunction_service.find_next_conjunction(target_date)
    candidate_evening, candidate_note = candidate_service.find_candidate_evening(location, next_conjunction)

    moon_data, crescent_eval = moon_service.calculate(
        location,
        candidate_evening,
        conjunction_dt=next_conjunction,
    )
    odeh_result = visibility_service.evaluate(moon_data)

    print(f"City: {location.name}")
    print(f"Gregorian Date: {target_date.isoformat()}")
    print()

    print("Prayer Times")
    print(f"Fajr:    {fmt_dt(prayer_times.fajr)}")
    print(f"Sunrise: {fmt_dt(prayer_times.sunrise)}")
    print(f"Dhuhr:   {fmt_dt(prayer_times.dhuhr)}")
    print(f"Asr:     {fmt_dt(prayer_times.asr)}")
    print(f"Maghrib: {fmt_dt(prayer_times.maghrib)}")
    print(f"Isha:    {fmt_dt(prayer_times.isha)}")
    print()

    print("Estimated Hijri Date")
    print(format_estimated_hijri(estimated_hijri))
    print()

    print("Next New Moon Conjunction")
    print(fmt_dt(next_conjunction))
    print()

    print("Next Crescent Candidate Evening")
    print(candidate_evening.isoformat())
    print(candidate_note)
    print()

    print("Moon Data")
    print(f"Conjunction: {fmt_dt(moon_data.conjunction)}")
    print(f"Sunset:      {fmt_dt(moon_data.sunset)}")
    print(f"Moonset:     {fmt_dt(moon_data.moonset)}")
    print(f"Moon Age:    {fmt_float(moon_data.moon_age_hours, 2, ' h')}")
    print(f"Altitude:    {fmt_float(moon_data.altitude_deg, 2, ' deg')}")
    print(f"Elongation:  {fmt_float(moon_data.elongation_deg, 2, ' deg')}")
    print(f"Lag Time:    {fmt_lag(moon_data.lag_time_minutes)}")
    print()

    print("Scientific Visibility (Odeh Criterion)")
    print(f"ARCV:        {fmt_float(odeh_result.arcv_deg, 2, ' deg')}")
    print(f"W:           {fmt_float(odeh_result.w_arcmin, 4, ' arcmin')}")
    print(f"V Value:     {fmt_q(odeh_result.v_value)}")
    print(f"Zone:        {odeh_result.zone}")
    print(f"Explanation: {odeh_result.explanation}")
    print()

    print("Crescent Evaluation")
    print(f"Astronomical Status:       {crescent_eval.astronomical_status}")
    print(f"Mukth Status:              {crescent_eval.mukth_status}")
    print(f"Visibility Status:         {crescent_eval.visibility_status}")
    print(f"Jordan Operational Status: {crescent_eval.jordan_operational_status}")
    print(f"Official Status:           {crescent_eval.official_status}")
    print(f"Reason Summary:            {crescent_eval.reason_summary}")
    print(f"Detailed Reasoning:        {crescent_eval.detailed_reasoning}")
    print()

    if args.no_save:
        print("MySQL Save")
        print("Skipped because --no-save was supplied.")
        return

    print("MySQL Save")
    try:
        persistence = ResultsPersistenceService()
        run_id = persistence.save_all(
            location=location,
            gregorian_date=target_date,
            prayer_times=prayer_times,
            moon_data=moon_data,
            odeh_result=odeh_result,
            crescent_eval=crescent_eval,
        )
        print(f"Saved successfully. Run ID: {run_id}")
    except Exception as exc:
        print(f"Save failed: {exc}")


if __name__ == "__main__":
    main()
