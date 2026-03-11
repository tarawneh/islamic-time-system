# ============================================================================
# File Name   : estimation_service.py
# Title       : Estimated Hijri Date Service
# Version     : 0.3.2
# Build Date  : 2026-03-09 17:22:01 UTC
# Author      : Dr. Rami Tarawneh
# Company     : 7th Layer
# Project     : Islamic Time System
# Description : Estimated Hijri date using the civil/tabular Islamic calendar.
#               This is display-only and not an official Jordanian date.
# License     : GNU General Public License v3.0 or later
# ============================================================================

from __future__ import annotations
from dataclasses import dataclass
from datetime import date

HIJRI_MONTH_NAMES = [
    "Muharram","Safar","Rabi al-Awwal","Rabi al-Thani","Jumada al-Ula",
    "Jumada al-Akhirah","Rajab","Shaban","Ramadan","Shawwal",
    "Dhu al-Qadah","Dhu al-Hijjah",
]

@dataclass(slots=True)
class EstimatedHijriDate:
    day: int
    month: int
    year: int
    month_name: str
    source: str = "Calculated"

    def to_display_string(self) -> str:
        return f"{self.day} {self.month_name} {self.year} ({self.source})"

class HijriEstimationService:
    @staticmethod
    def _gregorian_to_jdn(g_date: date) -> int:
        year, month, day = g_date.year, g_date.month, g_date.day
        a = (14 - month) // 12
        y = year + 4800 - a
        m = month + 12 * a - 3
        return day + ((153 * m + 2) // 5) + 365 * y + y // 4 - y // 100 + y // 400 - 32045

    @staticmethod
    def _islamic_from_jdn(jdn: int) -> tuple[int, int, int]:
        l = jdn - 1948440 + 10632
        n = (l - 1) // 10631
        l = l - 10631 * n + 354
        j = ((10985 - l) // 5316) * ((50 * l) // 17719) + (l // 5670) * ((43 * l) // 15238)
        l = l - ((30 - j) // 15) * ((17719 * j) // 50) - (j // 16) * ((15238 * j) // 43) + 29
        month = (24 * l) // 709
        day = l - (709 * month) // 24
        year = 30 * n + j - 30
        return int(day), int(month), int(year)

    def estimate(self, g_date: date) -> EstimatedHijriDate:
        jdn = self._gregorian_to_jdn(g_date)
        day, month, year = self._islamic_from_jdn(jdn)
        return EstimatedHijriDate(day, month, year, HIJRI_MONTH_NAMES[month - 1])
