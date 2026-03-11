
"""
File: sky_brightness.py
Version: 0.7.6
Build: 2026-03-11 22:41 UTC
Author: Dr. Rami Tarawneh
Company: 7th Layer
Project: Islamic Time System
License: GNU GPL

Description:
Foundation model estimating twilight sky brightness near sunset.
"""

import math

class SkyBrightnessModel:

    def compute(self, solar_altitude_deg: float) -> float:
        depression = -solar_altitude_deg
        if depression < 0:
            return 1.0
        brightness = math.exp(-0.25 * depression)
        return max(0.0, min(1.0, brightness))
