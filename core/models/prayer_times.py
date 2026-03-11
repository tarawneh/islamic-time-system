from dataclasses import dataclass
from typing import Optional

@dataclass
class PrayerTimes:
    fajr: Optional[object]
    sunrise: Optional[object]
    dhuhr: Optional[object]
    asr: Optional[object]
    maghrib: Optional[object]
    isha: Optional[object]
    imsak: Optional[object] = None
    duha_start: Optional[object] = None
    zawal_start: Optional[object] = None
    midnight: Optional[object] = None
    last_third_start: Optional[object] = None
    qiyam_start: Optional[object] = None
    karaha_after_sunrise_end: Optional[object] = None
    karaha_before_zawal_start: Optional[object] = None
    karaha_before_zawal_end: Optional[object] = None
    karaha_after_asr_start: Optional[object] = None
    karaha_after_asr_end: Optional[object] = None
    profile_code: Optional[str] = None
