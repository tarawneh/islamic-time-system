from __future__ import annotations
from dataclasses import dataclass
from datetime import timedelta
from core.models.prayer_times import PrayerTimes

try:
    from modules.reference.prayer_profile_repository import PrayerProfileRepository
except Exception:
    PrayerProfileRepository = None

@dataclass
class WorkingPrayerProfile:
    profile_code: str = "JO_OFFICIAL_WORKING"
    fajr_angle_deg: float = 18.0
    isha_angle_deg: float = 17.0
    asr_method: str = "SHAFII"
    imsak_offset_minutes: int = 10
    duha_offset_minutes: int = 15
    zawal_offset_minutes: int = 5
    midnight_method: str = "SUNSET_TO_FAJR"
    qiyam_method: str = "LAST_THIRD"
    karaha_after_sunrise_minutes: int = 15
    karaha_before_zawal_minutes: int = 5
    karaha_after_asr_to_maghrib: int = 1

class PrayerTimeService:
    def __init__(self, astronomy_engine) -> None:
        self.astronomy_engine = astronomy_engine
        self.profile_repo = PrayerProfileRepository() if PrayerProfileRepository is not None else None

    def calculate(self, location, target_date, profile_code: str = "JO_OFFICIAL_WORKING") -> PrayerTimes:
        profile = self._load_profile(profile_code)
        sunrise = self.astronomy_engine.get_sunrise(location, target_date)
        sunset = self.astronomy_engine.get_sunset(location, target_date)
        dhuhr = self.astronomy_engine.get_solar_noon(location, target_date)
        fajr = self._offset_from_sunrise(sunrise, float(profile.fajr_angle_deg), before=True)
        isha = self._offset_from_sunset(sunset, float(profile.isha_angle_deg), after=True)
        asr = self._estimate_asr(dhuhr, sunset, profile.asr_method)
        imsak = fajr - timedelta(minutes=int(profile.imsak_offset_minutes)) if fajr else None
        duha_start = sunrise + timedelta(minutes=int(profile.duha_offset_minutes)) if sunrise else None
        zawal_start = dhuhr - timedelta(minutes=int(profile.zawal_offset_minutes)) if dhuhr else None
        next_sunrise = self.astronomy_engine.get_sunrise(location, target_date + timedelta(days=1))
        next_fajr = self._offset_from_sunrise(next_sunrise, float(profile.fajr_angle_deg), before=True)
        midnight = last_third_start = qiyam_start = None
        if sunset and next_fajr:
            night_duration = next_fajr - sunset
            midnight = sunset + night_duration / 2
            last_third_start = sunset + (night_duration * 2 / 3)
            qiyam_start = last_third_start
        karaha_after_sunrise_end = sunrise + timedelta(minutes=int(profile.karaha_after_sunrise_minutes)) if sunrise else None
        karaha_before_zawal_start = dhuhr - timedelta(minutes=int(profile.karaha_before_zawal_minutes)) if dhuhr else None
        karaha_before_zawal_end = dhuhr
        karaha_after_asr_start = asr
        karaha_after_asr_end = sunset if int(profile.karaha_after_asr_to_maghrib or 0) == 1 else None
        return PrayerTimes(fajr=fajr, sunrise=sunrise, dhuhr=dhuhr, asr=asr, maghrib=sunset, isha=isha, imsak=imsak, duha_start=duha_start, zawal_start=zawal_start, midnight=midnight, last_third_start=last_third_start, qiyam_start=qiyam_start, karaha_after_sunrise_end=karaha_after_sunrise_end, karaha_before_zawal_start=karaha_before_zawal_start, karaha_before_zawal_end=karaha_before_zawal_end, karaha_after_asr_start=karaha_after_asr_start, karaha_after_asr_end=karaha_after_asr_end, profile_code=profile.profile_code)

    def _load_profile(self, profile_code: str) -> WorkingPrayerProfile:
        if self.profile_repo is not None:
            try:
                row = self.profile_repo.get_rules_by_profile_code(profile_code)
                if row:
                    return WorkingPrayerProfile(profile_code=row["profile_code"], fajr_angle_deg=float(row["fajr_angle_deg"]), isha_angle_deg=float(row["isha_angle_deg"]), asr_method=row["asr_method"], imsak_offset_minutes=int(row["imsak_offset_minutes"] or 10), duha_offset_minutes=int(row["duha_offset_minutes"] or 15), zawal_offset_minutes=int(row["zawal_offset_minutes"] or 5), midnight_method=row["midnight_method"], qiyam_method=row["qiyam_method"], karaha_after_sunrise_minutes=int(row["karaha_after_sunrise_minutes"] or 15), karaha_before_zawal_minutes=int(row["karaha_before_zawal_minutes"] or 5), karaha_after_asr_to_maghrib=int(row["karaha_after_asr_to_maghrib"] or 1))
            except Exception:
                pass
        return WorkingPrayerProfile(profile_code=profile_code)

    @staticmethod
    def _angle_to_minutes(angle_deg: float) -> int:
        return int(round(angle_deg * 4.56))

    def _offset_from_sunrise(self, sunrise, angle_deg: float, before: bool = True):
        if sunrise is None:
            return None
        minutes = self._angle_to_minutes(angle_deg)
        return sunrise - timedelta(minutes=minutes) if before else sunrise + timedelta(minutes=minutes)

    def _offset_from_sunset(self, sunset, angle_deg: float, after: bool = True):
        if sunset is None:
            return None
        minutes = self._angle_to_minutes(angle_deg)
        return sunset + timedelta(minutes=minutes) if after else sunset - timedelta(minutes=minutes)

    @staticmethod
    def _estimate_asr(dhuhr, sunset, asr_method: str):
        if dhuhr is None or sunset is None:
            return None
        day_half = sunset - dhuhr
        fraction = 0.62 if (asr_method or "").upper() == "SHAFII" else 0.72
        return dhuhr + day_half * fraction
