
"""
File: contrast.py
Version: 0.7.6
Build: 2026-03-11 22:41 UTC
Author: Dr. Rami Tarawneh
Company: 7th Layer
Project: Islamic Time System
License: GNU GPL

Description:
Computes contrast between crescent brightness and twilight sky brightness.
"""

class ContrastModel:

    def compute(self, crescent_brightness: float, sky_brightness: float) -> float:
        if sky_brightness <= 0:
            return float("inf")
        return crescent_brightness / sky_brightness
