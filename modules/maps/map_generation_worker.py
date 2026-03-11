# ============================================================================
# File Name   : map_generation_worker.py
# Version     : 0.7.2
# Author      : Dr. Rami Tarawneh
# Company     : 7th Layer
# Project     : Islamic Time System
# Description : Worker object for background world-map generation.
# License     : GNU General Public License v3.0 or later
# ============================================================================
from __future__ import annotations
from PySide6.QtCore import QObject, Signal, Slot

class MapGenerationWorker(QObject):
    progress_changed = Signal(int, str)
    finished = Signal(dict, dict, str)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, generator, target_date, resolution_deg, criterion_name, adaptive_enabled,
                 adaptive_resolution_deg, adaptive_zoom_threshold, basemap, date_mode_text=""):
        super().__init__()
        self.generator = generator
        self.target_date = target_date
        self.resolution_deg = resolution_deg
        self.criterion_name = criterion_name
        self.adaptive_enabled = adaptive_enabled
        self.adaptive_resolution_deg = adaptive_resolution_deg
        self.adaptive_zoom_threshold = adaptive_zoom_threshold
        self.basemap = basemap
        self.date_mode_text = date_mode_text
        self._cancel_requested = False

    def request_cancel(self) -> None:
        self._cancel_requested = True

    def _is_cancelled(self) -> bool:
        return self._cancel_requested

    def _report_progress(self, percent: int, message: str) -> None:
        self.progress_changed.emit(percent, message)

    @Slot()
    def run(self) -> None:
        try:
            feature_collection, stats = self.generator.generate_world_map(
                target_date=self.target_date,
                resolution_deg=self.resolution_deg,
                criterion_name=self.criterion_name,
                adaptive_enabled=self.adaptive_enabled,
                adaptive_resolution_deg=self.adaptive_resolution_deg,
                adaptive_zoom_threshold=self.adaptive_zoom_threshold,
                progress_callback=self._report_progress,
                cancel_callback=self._is_cancelled,
                date_mode_text=self.date_mode_text,
            )
            if self._cancel_requested:
                self.cancelled.emit()
                return
            self.finished.emit(feature_collection, stats, self.basemap)
        except InterruptedError:
            self.cancelled.emit()
        except Exception as exc:
            self.failed.emit(str(exc))
