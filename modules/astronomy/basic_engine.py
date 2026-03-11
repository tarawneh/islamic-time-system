# ============================================================================
# File Name   : basic_engine.py
# Title       : Basic Astronomy Engine
# Version     : 0.7.5
# Build Date  : 2026-03-11 00:00:00 UTC
# Author      : Dr. Rami Tarawneh
# Company     : 7th Layer
# Project     : Islamic Time System
# Description : Skyfield-backed astronomy engine for sunrise, sunset, moonrise,
#               moonset, conjunction lookup, lunar altitude, solar altitude,
#               ARCV, apparent elongation, crescent width, and lag.
#
#               v0.7.5 is the first cleanup pass for the scientific reference
#               model discussed during the crescent-visibility review. The main
#               goals of this version are:
#
#               1) Keep all sunset-based lunar visibility metrics in one
#                  consistent observer frame: apparent + topocentric.
#               2) Use explicit horizon definitions for rise/set events instead
#                  of silently relying on an implicit center-on-horizon model.
#               3) Expose intermediate scientific values like solar altitude at
#                  sunset and ARCV so later modules do not need to re-derive
#                  them independently.
#
#               Important implementation note:
#               - Conjunction remains geocentric because the astronomical new
#                 moon phase event itself is not a local observer event.
#               - Observation metrics remain topocentric because crescent
#                 visibility is inherently observer-dependent.
# License     : GNU General Public License v3.0 or later
# ============================================================================

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from math import asin, cos, degrees, radians
from typing import Optional
from zoneinfo import ZoneInfo

from skyfield import almanac
from skyfield.api import Loader, wgs84

from core.interfaces.astronomy_engine import AstronomyEngine
from core.models.location import Location


class BasicAstronomyEngine(AstronomyEngine):
    # ------------------------------------------------------------------
    # Scientific constants used by the engine.
    #
    # STANDARD_SUN_EVENT_ALTITUDE_DEG:
    #   The conventional apparent center altitude used for sunrise/sunset.
    #   It combines standard refraction near the horizon with the apparent
    #   solar semi-diameter and corresponds to the familiar -0.833 deg.
    #
    # STANDARD_MOON_EVENT_ALTITUDE_DEG:
    #   The commonly used apparent center altitude for moonrise/moonset in
    #   practical calendrical applications. This value is not perfectly
    #   dynamic because true lunar semi-diameter varies slightly with range,
    #   but it is a major improvement over using 0.0 deg for the lunar center.
    #
    # STANDARD_REFRACTION_DEG:
    #   Preserved here because later versions may promote it into a dynamic
    #   pressure/temperature-aware model.
    # ------------------------------------------------------------------
    STANDARD_SUN_EVENT_ALTITUDE_DEG = -0.833
    STANDARD_MOON_EVENT_ALTITUDE_DEG = -0.727
    STANDARD_REFRACTION_DEG = 34.0 / 60.0
    NOMINAL_LUNAR_RADIUS_KM = 1737.4

    def __init__(self, data_dir: str = ".skyfield") -> None:
        self.loader = Loader(data_dir)
        self.ts = self.loader.timescale()
        self.eph = self.loader("de421.bsp")
        self.earth = self.eph["earth"]
        self.sun = self.eph["sun"]
        self.moon = self.eph["moon"]

    @staticmethod
    def _tz(location: Location) -> ZoneInfo:
        return ZoneInfo(location.timezone)

    @staticmethod
    def _topos(location: Location):
        return wgs84.latlon(
            latitude_degrees=location.latitude,
            longitude_degrees=location.longitude,
            elevation_m=location.elevation_meters,
        )

    def _observer(self, location: Location):
        return self.earth + self._topos(location)

    def _build_rise_set_event_function(self, location: Location, body_name: str, horizon_degrees: float):
        """
        Build a Skyfield rise/set predicate using an explicit horizon angle.

        Why this helper exists:
        - We want the event definition to be obvious in code review.
        - Future versions may inject a pressure/temperature-aware horizon here.
        - We keep a compatibility fallback in case an older Skyfield build does
          not support the horizon_degrees keyword in the runtime environment.
        """
        try:
            return almanac.risings_and_settings(
                self.eph,
                self.eph[body_name],
                self._topos(location),
                horizon_degrees=horizon_degrees,
            )
        except TypeError:
            # ----------------------------------------------------------------
            # Compatibility fallback.
            # This preserves backward runtime compatibility with older Skyfield
            # signatures, though the preferred path is the explicit horizon
            # branch above.
            # ----------------------------------------------------------------
            return almanac.risings_and_settings(
                self.eph,
                self.eph[body_name],
                self._topos(location),
            )

    def _daily_event(
        self,
        location: Location,
        target_date: date,
        is_rise: bool,
        body_name: str,
        horizon_degrees: float,
    ) -> Optional[datetime]:
        """
        Resolve one rise or set event during the local civil day.

        The search window runs from local midnight to the next local midnight,
        converted to UTC for the ephemeris. The event function itself uses the
        explicit horizon definition supplied by the caller so that:

        - sun events use the standard apparent upper-limb convention
        - moon events use a corrected upper-limb approximation instead of an
          incorrect 0 deg center-on-horizon assumption
        """
        tz = self._tz(location)
        local_start = datetime.combine(target_date, time(0, 0, 0), tzinfo=tz)
        local_end = local_start + timedelta(days=1)
        t0 = self.ts.from_datetime(local_start.astimezone(timezone.utc))
        t1 = self.ts.from_datetime(local_end.astimezone(timezone.utc))

        event_fn = self._build_rise_set_event_function(
            location=location,
            body_name=body_name,
            horizon_degrees=horizon_degrees,
        )
        times, states = almanac.find_discrete(t0, t1, event_fn)
        desired = True if is_rise else False
        for t, state in zip(times, states):
            if bool(state) == desired:
                return t.utc_datetime().replace(tzinfo=timezone.utc).astimezone(tz)
        return None

    def get_sunrise(self, location: Location, target_date: date) -> Optional[datetime]:
        return self._daily_event(
            location=location,
            target_date=target_date,
            is_rise=True,
            body_name="sun",
            horizon_degrees=self.STANDARD_SUN_EVENT_ALTITUDE_DEG,
        )

    def get_sunset(self, location: Location, target_date: date) -> Optional[datetime]:
        return self._daily_event(
            location=location,
            target_date=target_date,
            is_rise=False,
            body_name="sun",
            horizon_degrees=self.STANDARD_SUN_EVENT_ALTITUDE_DEG,
        )

    def get_moonrise(self, location: Location, target_date: date) -> Optional[datetime]:
        return self._daily_event(
            location=location,
            target_date=target_date,
            is_rise=True,
            body_name="moon",
            horizon_degrees=self.STANDARD_MOON_EVENT_ALTITUDE_DEG,
        )

    def get_moonset(self, location: Location, target_date: date) -> Optional[datetime]:
        return self._daily_event(
            location=location,
            target_date=target_date,
            is_rise=False,
            body_name="moon",
            horizon_degrees=self.STANDARD_MOON_EVENT_ALTITUDE_DEG,
        )

    def get_solar_noon(self, location: Location, target_date: date) -> Optional[datetime]:
        sunrise = self.get_sunrise(location, target_date)
        sunset = self.get_sunset(location, target_date)
        if sunrise is None or sunset is None:
            tz = self._tz(location)
            return datetime.combine(target_date, time(12, 0, 0), tzinfo=tz)
        return sunrise + (sunset - sunrise) / 2

    def get_conjunction(self, target_date: date) -> Optional[datetime]:
        """
        Resolve the nearest geocentric new moon phase around the target date.

        This intentionally stays geocentric. The new moon phase event is a
        global Earth-Moon-Sun geometry event, not an observer-local horizon
        event. Making this explicit prevents future confusion when comparing
        moon age with topocentric observation metrics.
        """
        center = datetime.combine(target_date, time(12, 0, 0), tzinfo=timezone.utc)
        start = center - timedelta(days=3)
        end = center + timedelta(days=3)
        t0 = self.ts.from_datetime(start)
        t1 = self.ts.from_datetime(end)
        moon_phases = almanac.moon_phases(self.eph)
        times, phases = almanac.find_discrete(t0, t1, moon_phases)
        candidates = []
        for t, phase in zip(times, phases):
            if int(phase) == 0:
                candidates.append(t.utc_datetime().replace(tzinfo=timezone.utc))
        if not candidates:
            return None
        return min(candidates, key=lambda dt: abs(dt - center))

    def _sun_moon_apparent(self, location: Location, dt_local: datetime):
        t = self.ts.from_datetime(dt_local.astimezone(timezone.utc))
        observer = self._observer(location)
        apparent_sun = observer.at(t).observe(self.sun).apparent()
        apparent_moon = observer.at(t).observe(self.moon).apparent()
        return apparent_sun, apparent_moon

    def _sunset_apparent_bundle(self, location: Location, target_date: date):
        """
        Return a single bundle of sunset-referenced apparent quantities.

        This helper is central to v0.7.5. It guarantees that all sunset-based
        visibility numbers come from one exact instant and one observer frame.
        That directly addresses the earlier risk of mixing event references when
        computing altitude, elongation, ARCV, and lag-related diagnostics.
        """
        sunset = self.get_sunset(location, target_date)
        if sunset is None:
            return None

        apparent_sun, apparent_moon = self._sun_moon_apparent(location, sunset)
        sun_alt, _sun_az, _sun_distance = apparent_sun.altaz()
        moon_alt, _moon_az, moon_distance = apparent_moon.altaz()
        elongation_deg = float(apparent_sun.separation_from(apparent_moon).degrees)

        distance_km = float(moon_distance.km)
        angular_radius_deg = degrees(asin(self.NOMINAL_LUNAR_RADIUS_KM / distance_km))
        angular_diameter_arcmin = angular_radius_deg * 2.0 * 60.0
        illuminated_fraction = (1.0 - cos(radians(elongation_deg))) / 2.0
        crescent_width_arcmin = angular_diameter_arcmin * illuminated_fraction

        return {
            "sunset": sunset,
            "sun_altitude_deg": float(sun_alt.degrees),
            "moon_altitude_deg": float(moon_alt.degrees),
            "elongation_deg": elongation_deg,
            "arcv_deg": float(moon_alt.degrees - sun_alt.degrees),
            "crescent_width_arcmin": float(crescent_width_arcmin),
        }

    def get_moon_altitude_at_sunset(self, location: Location, target_date: date) -> Optional[float]:
        bundle = self._sunset_apparent_bundle(location, target_date)
        return None if bundle is None else bundle["moon_altitude_deg"]

    def get_solar_altitude_at_sunset(self, location: Location, target_date: date) -> Optional[float]:
        bundle = self._sunset_apparent_bundle(location, target_date)
        return None if bundle is None else bundle["sun_altitude_deg"]

    def get_arcv_at_sunset(self, location: Location, target_date: date) -> Optional[float]:
        bundle = self._sunset_apparent_bundle(location, target_date)
        return None if bundle is None else bundle["arcv_deg"]

    def get_elongation_at_sunset(self, location: Location, target_date: date) -> Optional[float]:
        bundle = self._sunset_apparent_bundle(location, target_date)
        return None if bundle is None else bundle["elongation_deg"]

    def get_crescent_width_arcmin_at_sunset(self, location: Location, target_date: date) -> Optional[float]:
        bundle = self._sunset_apparent_bundle(location, target_date)
        return None if bundle is None else bundle["crescent_width_arcmin"]

    def get_lag_time_minutes(self, location: Location, target_date: date) -> Optional[float]:
        """
        Return moonset minus sunset in minutes.

        The scientific point is not the subtraction itself; the important part
        is that both inputs come from the same engine and explicit horizon model.
        That removes one of the most common hidden inconsistencies in crescent
        software, where sunset and moonset are sometimes computed using
        different conventions.
        """
        sunset = self.get_sunset(location, target_date)
        moonset = self.get_moonset(location, target_date)
        if sunset is None or moonset is None:
            return None
        return (moonset - sunset).total_seconds() / 60.0
