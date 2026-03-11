# ============================================================================
# File Name   : visibility_map_generator.py
# Version     : 0.7.2
# Author      : Dr. Rami Tarawneh
# Company     : 7th Layer
# Project     : Islamic Time System
# Description : Global visibility map generator. Produces semi-transparent
#               rectangular GeoJSON cells instead of point markers.
# License     : GNU General Public License v3.0 or later
# ============================================================================
from __future__ import annotations
from core.models.location import Location

class VisibilityMapGenerator:
    def __init__(self, moon_service, visibility_service):
        self.moon_service = moon_service
        self.visibility_service = visibility_service

    def generate_world_map(self, target_date, resolution_deg, criterion_name, adaptive_enabled,
                           adaptive_resolution_deg, adaptive_zoom_threshold, progress_callback=None,
                           cancel_callback=None, date_mode_text=""):
        features = []
        lat_values = self._frange(-60.0, 60.0, resolution_deg)
        lon_values = self._frange(-180.0, 180.0, resolution_deg)
        total_points = len(lat_values) * len(lon_values)
        completed = 0
        half = float(resolution_deg) / 2.0

        for lat in lat_values:
            for lon in lon_values:
                if cancel_callback is not None and cancel_callback():
                    raise InterruptedError("Map generation cancelled by user.")
                location = Location(name="grid", latitude=lat, longitude=lon, elevation_meters=0.0, timezone="UTC")
                try:
                    moon_data, _ = self.moon_service.calculate(location, target_date)
                    results = self.visibility_service.evaluate_all(moon_data)
                    selected = self._select_result(results, criterion_name)
                    category = self._normalize_category(selected)
                    raw_value = getattr(selected, "raw_value", None) if selected else None
                    criterion_label = getattr(selected, "criterion_name", criterion_name) if selected else criterion_name
                except Exception:
                    category = "Undetermined"
                    raw_value = None
                    criterion_label = criterion_name

                west = max(-180.0, lon - half)
                east = min(180.0, lon + half)
                south = max(-90.0, lat - half)
                north = min(90.0, lat + half)

                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": [[
                        [west, south], [east, south], [east, north], [west, north], [west, south]
                    ]]},
                    "properties": {
                        "criterion": criterion_label,
                        "category": category,
                        "raw_value": raw_value,
                        "lat": lat,
                        "lon": lon,
                        "resolution_deg": resolution_deg,
                    },
                })
                completed += 1
                if progress_callback is not None:
                    percent = int((completed / total_points) * 100)
                    progress_callback(percent, f"جاري توليد الخريطة... {completed} / {total_points} خلية")

        stats = {
            "target_date": str(target_date),
            "date_mode_text": date_mode_text,
            "resolution_deg": resolution_deg,
            "point_count": len(features),
            "criterion_name": criterion_name,
            "adaptive_enabled": adaptive_enabled,
            "adaptive_resolution_deg": adaptive_resolution_deg,
            "adaptive_zoom_threshold": adaptive_zoom_threshold,
        }
        return {"type": "FeatureCollection", "features": features}, stats

    @staticmethod
    def _frange(start, stop, step):
        vals = []
        cur = start
        while cur <= stop + 1e-9:
            vals.append(round(cur, 6))
            cur += step
        return vals

    @staticmethod
    def _select_result(results, criterion_name):
        if criterion_name == "consensus":
            return VisibilityMapGenerator._build_consensus_result(results)
        for result in results:
            if getattr(result, "criterion_name", "") == criterion_name:
                return result
        return None

    @staticmethod
    def _build_consensus_result(results):
        odeh = yallop = danjon = None
        for result in results:
            name = getattr(result, "criterion_name", "")
            if name == "Odeh":
                odeh = result
            elif name == "Yallop":
                yallop = result
            elif name == "Danjon":
                danjon = result

        class ConsensusResult:
            criterion_name = "Consensus"
            raw_value = None
            category = "Undetermined"
            explanation = ""

        consensus = ConsensusResult()
        if danjon is not None and getattr(danjon, "category", "") == "Below limit":
            consensus.category = "Not Visible"
            return consensus

        odeh_cat = getattr(odeh, "category", "")
        yallop_cat = getattr(yallop, "category", "")

        if odeh_cat in ("A", "B") and yallop_cat in ("A", "B"):
            consensus.category = "Visible"
        elif odeh_cat == "C" or yallop_cat in ("C", "D"):
            consensus.category = "Optical Aid"
        elif yallop_cat in ("E", "F"):
            consensus.category = "Not Visible"
        return consensus

    @staticmethod
    def _normalize_category(result):
        if result is None:
            return "Undetermined"
        category = getattr(result, "category", "Undetermined")
        criterion = getattr(result, "criterion_name", "")
        if criterion == "Odeh":
            if category in ("A", "B"): return "Visible"
            if category == "C": return "Optical Aid"
            return "Not Visible"
        if criterion == "Yallop":
            if category in ("A", "B"): return "Visible"
            if category in ("C", "D"): return "Optical Aid"
            return "Not Visible"
        return category
