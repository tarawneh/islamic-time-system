# ============================================================================
# File Name   : location.py
# Title       : Location Model
# Version     : 0.3.2
# Build Date  : 2026-03-09 17:22:01 UTC
# Author      : Dr. Rami Tarawneh
# Company     : 7th Layer
# Project     : Islamic Time System
# Description : Shared location model.
# License     : GNU General Public License v3.0 or later
# ============================================================================

from __future__ import annotations
from dataclasses import dataclass

@dataclass(slots=True)
class Location:
    name: str
    latitude: float
    longitude: float
    elevation_meters: float
    timezone: str
