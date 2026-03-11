# ============================================================================
# File Name   : gui_main_ar.py
# Version     : 0.7.4
# Author      : Dr. Rami Tarawneh
# Company     : 7th Layer
# Project     : Islamic Time System
# Description : Arabic GUI update that restores additional daily prayer times,
#               adds Arabic weekday names to daily views, and introduces a
#               monthly calendar tab with copy/export support.
# License     : GNU General Public License v3.0 or later
# ============================================================================
from __future__ import annotations

import calendar
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu --disable-gpu-compositing")
os.environ.setdefault("QT_OPENGL", "software")
os.environ.setdefault("QT_QUICK_BACKEND", "software")

from PySide6.QtCore import QDate, Qt, QThread
from PySide6.QtGui import QBrush, QColor, QCursor, QTextCharFormat
from PySide6.QtWidgets import (
    QApplication, QCalendarWidget, QCheckBox, QComboBox, QDateEdit, QDialog,
    QDialogButtonBox, QDoubleSpinBox, QFileDialog, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
    QProgressBar, QPushButton, QRadioButton, QSpinBox, QSplitter, QTabWidget,
    QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)

from core.models.location import Location
from modules.astronomy.basic_engine import BasicAstronomyEngine
from modules.hijri.conjunction_service import ConjunctionService
from modules.hijri.crescent_candidate_service import CrescentCandidateService
from modules.hijri.estimation_service import HijriEstimationService
from modules.maps.leaflet_map_view import LeafletMapView
from modules.maps.map_generation_worker import MapGenerationWorker
from modules.maps.visibility_map_generator import VisibilityMapGenerator
from modules.moon.service import MoonService
from modules.moon_visibility.service import MoonVisibilityService
from modules.prayer_times.service import PrayerTimeService
from modules.reference.reference_repository import ReferenceRepository

try:
    from modules.storage.results_persistence_service import ResultsPersistenceService
except Exception:
    ResultsPersistenceService = None

try:
    from results_query_repository import ResultsQueryRepository
except Exception:
    ResultsQueryRepository = None

try:
    from openpyxl import Workbook
except Exception:
    Workbook = None

AR_WEEKDAYS = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
AR_MONTHS_GREGORIAN = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
AR_MONTHS_HIJRI = ["محرم", "صفر", "ربيع الأول", "ربيع الآخر", "جمادى الأولى", "جمادى الآخرة", "رجب", "شعبان", "رمضان", "شوال", "ذو القعدة", "ذو الحجة"]


class SavedRunsBrowserDialog(QDialog):
    def __init__(self, repo, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.selected_run = None
        self.setWindowTitle("استعراض التشغيلات المحفوظة")
        self.resize(760, 520)

        root = QVBoxLayout(self)
        self.info_label = QLabel("اختر يومًا من الرزنامة. الأيام التي تحتوي تشغيلات محفوظة مميزة باللون.")
        root.addWidget(self.info_label)

        self.calendar = QCalendarWidget()
        root.addWidget(self.calendar)

        self.list_widget = QListWidget()
        root.addWidget(self.list_widget, 1)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setText("استرجاع التشغيل")
        self.button_box.button(QDialogButtonBox.Cancel).setText("إلغاء")
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        root.addWidget(self.button_box)

        self.calendar.selectionChanged.connect(self._load_runs_for_selected_day)
        self.calendar.currentPageChanged.connect(self._highlight_current_month)
        self.list_widget.itemSelectionChanged.connect(self._update_ok_button)
        self.button_box.accepted.connect(self._accept_selection)
        self.button_box.rejected.connect(self.reject)

        self._highlight_current_month()
        self._load_runs_for_selected_day()

    def _highlight_current_month(self):
        year = self.calendar.yearShown()
        month = self.calendar.monthShown()
        default_fmt = QTextCharFormat()
        for day in range(1, 32):
            self.calendar.setDateTextFormat(QDate(year, month, day), default_fmt)

        fmt = QTextCharFormat()
        fmt.setBackground(QBrush(QColor("#fff3cd")))
        fmt.setForeground(QBrush(QColor("#7a4f00")))
        fmt.setFontWeight(700)

        try:
            days = self.repo.get_days_with_runs_for_month(year, month)
        except Exception:
            days = []

        for day in days:
            self.calendar.setDateTextFormat(QDate(year, month, day), fmt)

    def _load_runs_for_selected_day(self):
        qdate = self.calendar.selectedDate()
        date_iso = qdate.toPython().isoformat()
        self.list_widget.clear()
        try:
            runs = self.repo.get_runs_for_day(date_iso)
        except Exception:
            runs = []
        for run in runs:
            item = QListWidgetItem(f"Run ID: {run.get('id')} | {run.get('city')} | {run.get('created_at')}")
            item.setData(Qt.UserRole, run)
            self.list_widget.addItem(item)
        self._update_ok_button()

    def _update_ok_button(self):
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(self.list_widget.currentItem() is not None)

    def _accept_selection(self):
        item = self.list_widget.currentItem()
        if item is None:
            return
        self.selected_run = item.data(Qt.UserRole)
        self.accept()


class ArabicMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("نظام المواقيت والأهلة")
        self.resize(1480, 980)
        self.config_path = Path("gui") / "gui_config_ar.json"
        self.reference_repo = ReferenceRepository()
        self.astronomy_engine = BasicAstronomyEngine()
        self.prayer_service = PrayerTimeService(self.astronomy_engine)
        self.moon_service = MoonService(self.astronomy_engine)
        self.visibility_service = MoonVisibilityService()
        self.hijri_service = HijriEstimationService()
        self.conjunction_service = ConjunctionService(self.astronomy_engine)
        self.candidate_service = CrescentCandidateService(self.astronomy_engine)
        self.map_generator = VisibilityMapGenerator(self.moon_service, self.visibility_service)
        self.map_thread = None
        self.map_worker = None
        self.last_map_feature_collection = None
        self.last_map_stats = None
        self.monthly_rows = []
        self._build_ui()
        self._refresh_monthly_year_mode()
        self._load_countries()
        self._wire_events()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        title = QLabel("نظام المواقيت والأهلة")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 26px; font-weight: 700;")
        root.addWidget(title)

        subtitle = QLabel("واجهة عربية تعتمد على MySQL وتعرض المقارنة العلمية مع خريطة رؤية عالمية")
        subtitle.setAlignment(Qt.AlignCenter)
        root.addWidget(subtitle)

        top_box = QGroupBox("بيانات الإدخال")
        top_layout = QGridLayout(top_box)
        self.country_combo = QComboBox()
        self.city_combo = QComboBox()
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())
        self.save_checkbox = QCheckBox("حفظ النتائج في MySQL")
        self.save_checkbox.setChecked(True)
        self.calc_button = QPushButton("احسب")
        self.latest_button = QPushButton("استعراض التشغيلات المحفوظة")
        top_layout.addWidget(QLabel("الدولة"), 0, 0)
        top_layout.addWidget(self.country_combo, 0, 1)
        top_layout.addWidget(QLabel("المدينة"), 0, 2)
        top_layout.addWidget(self.city_combo, 0, 3)
        top_layout.addWidget(QLabel("التاريخ الميلادي"), 1, 0)
        top_layout.addWidget(self.date_edit, 1, 1)
        top_layout.addWidget(self.save_checkbox, 1, 2)
        top_layout.addWidget(self.calc_button, 1, 3)
        top_layout.addWidget(self.latest_button, 2, 3)
        root.addWidget(top_box)

        splitter = QSplitter()
        splitter.setOrientation(Qt.Horizontal)
        root.addWidget(splitter, 1)
        self.tabs = QTabWidget()
        splitter.addWidget(self.tabs)
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        splitter.addWidget(self.summary_text)
        splitter.setSizes([1140, 260])
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 1)

        self.prayer_tab = self._make_text_tab()
        self.hijri_tab = self._make_text_tab()
        self.moon_tab = self._make_text_tab()
        self.science_tab = self._make_text_tab()
        self.operational_tab = self._make_text_tab()
        self.storage_tab = self._make_text_tab()
        self.monthly_tab = self._build_monthly_tab()
        self.map_settings_tab = self._build_map_settings_tab()
        self.map_result_tab = self._build_map_result_tab()

        self.tabs.addTab(self.prayer_tab, "المواقيت اليومية")
        self.tabs.addTab(self.hijri_tab, "الهجري والهلال القادم")
        self.tabs.addTab(self.moon_tab, "بيانات الهلال")
        self.tabs.addTab(self.science_tab, "المعايير العلمية")
        self.tabs.addTab(self.operational_tab, "التقييم التشغيلي")
        self.tabs.addTab(self.storage_tab, "الحفظ والسجل")
        self.tabs.addTab(self.monthly_tab, "التقويم الشهري")
        self.tabs.addTab(self.map_settings_tab, "إعدادات خريطة الرؤية")
        self.tabs.addTab(self.map_result_tab, "خريطة الرؤية العالمية")

        self.status_label = QLabel("جاهز")
        root.addWidget(self.status_label)

    def _make_text_tab(self) -> QTextEdit:
        widget = QTextEdit()
        widget.setReadOnly(True)
        return widget

    def _build_monthly_tab(self) -> QWidget:
        tab = QWidget()
        root = QVBoxLayout(tab)
        box = QGroupBox("إعدادات التقويم الشهري")
        grid = QGridLayout(box)
        self.monthly_calendar_type_combo = QComboBox()
        self.monthly_calendar_type_combo.addItem("شهر ميلادي", "gregorian")
        self.monthly_calendar_type_combo.addItem("شهر هجري", "hijri")
        self.monthly_hijri_source_combo = QComboBox()
        self.monthly_hijri_source_combo.addItem("هجري حسابي", "calculated")
        self.monthly_hijri_source_combo.addItem("هجري رسمي للدولة (غير متوفر حاليًا)", "official")
        self.monthly_year_label = QLabel("السنة الميلادية")
        self.monthly_year_spin = QSpinBox()
        self.monthly_year_spin.setRange(1900, 2500)
        self.monthly_year_spin.setValue(date.today().year)
        self.monthly_month_combo = QComboBox()
        for idx, name in enumerate(AR_MONTHS_GREGORIAN, start=1):
            self.monthly_month_combo.addItem(name, idx)
        self.monthly_month_combo.setCurrentIndex(date.today().month - 1)
        self.monthly_generate_button = QPushButton("توليد التقويم الشهري")
        self.monthly_copy_button = QPushButton("نسخ الجدول")
        self.monthly_export_button = QPushButton("تصدير إلى Excel")
        grid.addWidget(QLabel("نوع التقويم"), 0, 0)
        grid.addWidget(self.monthly_calendar_type_combo, 0, 1)
        grid.addWidget(QLabel("مصدر الشهر الهجري"), 0, 2)
        grid.addWidget(self.monthly_hijri_source_combo, 0, 3)
        grid.addWidget(self.monthly_year_label, 1, 0)
        grid.addWidget(self.monthly_year_spin, 1, 1)
        grid.addWidget(QLabel("الشهر"), 1, 2)
        grid.addWidget(self.monthly_month_combo, 1, 3)
        grid.addWidget(self.monthly_generate_button, 2, 1)
        grid.addWidget(self.monthly_copy_button, 2, 2)
        grid.addWidget(self.monthly_export_button, 2, 3)
        root.addWidget(box)
        self.monthly_info_text = QTextEdit()
        self.monthly_info_text.setReadOnly(True)
        self.monthly_info_text.setMaximumHeight(110)
        root.addWidget(self.monthly_info_text)
        self.monthly_table = QTableWidget()
        self.monthly_table.setColumnCount(9)
        self.monthly_table.setHorizontalHeaderLabels(["اليوم", "التاريخ الميلادي", "التاريخ الهجري", "الفجر", "الشروق", "الظهر", "العصر", "المغرب", "العشاء"])
        root.addWidget(self.monthly_table, 1)
        return tab

    def _build_map_settings_tab(self) -> QWidget:
        tab = QWidget(); root = QVBoxLayout(tab)
        box = QGroupBox("إعدادات الخريطة"); grid = QGridLayout(box)
        self.map_date_auto_radio = QRadioButton("أول مساء صالح بعد الاقتران")
        self.map_date_manual_radio = QRadioButton("تاريخ يدوي للخريطة")
        self.map_date_auto_radio.setChecked(True)
        self.map_date_edit = QDateEdit(); self.map_date_edit.setCalendarPopup(True); self.map_date_edit.setDisplayFormat("yyyy-MM-dd"); self.map_date_edit.setDate(QDate.currentDate()); self.map_date_edit.setEnabled(False)
        self.map_resolution_combo = QComboBox(); self.map_resolution_combo.addItem("منخفضة (2.0°)", 2.0); self.map_resolution_combo.addItem("متوسطة (1.0°)", 1.0); self.map_resolution_combo.addItem("عالية (0.5°)", 0.5); self.map_resolution_combo.addItem("مخصصة", "custom"); self.map_resolution_combo.setCurrentIndex(0)
        self.map_resolution_custom = QDoubleSpinBox(); self.map_resolution_custom.setDecimals(2); self.map_resolution_custom.setRange(0.10, 5.00); self.map_resolution_custom.setSingleStep(0.10); self.map_resolution_custom.setValue(1.00); self.map_resolution_custom.setEnabled(False)
        self.map_style_combo = QComboBox(); self.map_style_combo.addItem("خريطة عادية", "osm"); self.map_style_combo.addItem("قمر صناعي", "satellite"); self.map_style_combo.addItem("هجين", "hybrid")
        self.map_criterion_combo = QComboBox(); self.map_criterion_combo.addItem("التوافق العلمي", "consensus"); self.map_criterion_combo.addItem("Odeh", "Odeh"); self.map_criterion_combo.addItem("Yallop", "Yallop"); self.map_criterion_combo.addItem("Danjon", "Danjon")
        self.adaptive_checkbox = QCheckBox("تفعيل الدقة التكيفية")
        self.adaptive_resolution_spin = QDoubleSpinBox(); self.adaptive_resolution_spin.setDecimals(2); self.adaptive_resolution_spin.setRange(0.10, 2.00); self.adaptive_resolution_spin.setSingleStep(0.05); self.adaptive_resolution_spin.setValue(0.25); self.adaptive_resolution_spin.setEnabled(False)
        self.adaptive_zoom_spin = QSpinBox(); self.adaptive_zoom_spin.setRange(2, 18); self.adaptive_zoom_spin.setValue(6); self.adaptive_zoom_spin.setEnabled(False)
        self.generate_map_button = QPushButton("توليد الخريطة"); self.cancel_map_button = QPushButton("إلغاء توليد الخريطة"); self.cancel_map_button.setEnabled(False)
        grid.addWidget(QLabel("تاريخ الخريطة"), 0, 0); grid.addWidget(self.map_date_auto_radio, 0, 1); grid.addWidget(self.map_date_manual_radio, 0, 2); grid.addWidget(self.map_date_edit, 0, 3)
        grid.addWidget(QLabel("الدقة الأساسية"), 1, 0); grid.addWidget(self.map_resolution_combo, 1, 1); grid.addWidget(QLabel("الدقة المخصصة"), 1, 2); grid.addWidget(self.map_resolution_custom, 1, 3)
        grid.addWidget(QLabel("نوع الخريطة"), 2, 0); grid.addWidget(self.map_style_combo, 2, 1); grid.addWidget(QLabel("المعيار"), 2, 2); grid.addWidget(self.map_criterion_combo, 2, 3)
        grid.addWidget(self.adaptive_checkbox, 3, 0); grid.addWidget(QLabel("الدقة المحلية"), 3, 1); grid.addWidget(self.adaptive_resolution_spin, 3, 2); grid.addWidget(QLabel("Zoom التفعيل"), 3, 3); grid.addWidget(self.adaptive_zoom_spin, 3, 4)
        grid.addWidget(self.generate_map_button, 4, 3); grid.addWidget(self.cancel_map_button, 4, 4)
        root.addWidget(box)
        self.progress_bar = QProgressBar(); self.progress_bar.setRange(0, 100); self.progress_bar.setValue(0); self.progress_bar.hide()
        self.progress_label = QLabel("0%"); self.progress_label.hide(); progress_row = QHBoxLayout(); progress_row.addWidget(self.progress_bar, 1); progress_row.addWidget(self.progress_label, 0); root.addLayout(progress_row)
        self.map_info_text = QTextEdit(); self.map_info_text.setReadOnly(True); root.addWidget(self.map_info_text, 1)
        return tab

    def _build_map_result_tab(self) -> QWidget:
        tab = QWidget(); root = QVBoxLayout(tab)
        top_row = QHBoxLayout(); top_row.addWidget(QLabel("تغيير نوع العرض بعد التوليد"))
        self.result_basemap_combo = QComboBox(); self.result_basemap_combo.addItem("خريطة عادية", "osm"); self.result_basemap_combo.addItem("قمر صناعي", "satellite"); self.result_basemap_combo.addItem("هجين", "hybrid"); top_row.addWidget(self.result_basemap_combo); top_row.addStretch(1); root.addLayout(top_row)
        self.result_map_note = QLabel("الخريطة ستظهر هنا بعد اكتمال التوليد."); root.addWidget(self.result_map_note)
        self.map_view = LeafletMapView(); self.map_view.setMinimumHeight(760); self.map_view.setMinimumWidth(1100); root.addWidget(self.map_view, 1)
        return tab

    def _wire_events(self) -> None:
        self.country_combo.currentIndexChanged.connect(self._refresh_cities)
        self.calc_button.clicked.connect(self._run_calculation)
        self.latest_button.clicked.connect(self._show_latest_saved_run)
        self.generate_map_button.clicked.connect(self._start_generate_visibility_map)
        self.cancel_map_button.clicked.connect(self._cancel_map_generation)
        self.map_resolution_combo.currentIndexChanged.connect(self._toggle_custom_resolution)
        self.adaptive_checkbox.toggled.connect(self._toggle_adaptive_controls)
        self.map_date_auto_radio.toggled.connect(self._toggle_map_date_mode)
        self.result_basemap_combo.currentIndexChanged.connect(self._rerender_last_map_with_new_basemap)
        self.monthly_calendar_type_combo.currentIndexChanged.connect(self._refresh_monthly_month_names)
        self.monthly_generate_button.clicked.connect(self._generate_monthly_calendar)
        self.monthly_copy_button.clicked.connect(self._copy_monthly_table)
        self.monthly_export_button.clicked.connect(self._export_monthly_table)

    def _toggle_map_date_mode(self, checked: bool) -> None:
        self.map_date_edit.setEnabled(not checked)

    def _toggle_custom_resolution(self) -> None:
        self.map_resolution_custom.setEnabled(self.map_resolution_combo.currentData() == "custom")

    def _toggle_adaptive_controls(self, checked: bool) -> None:
        self.adaptive_resolution_spin.setEnabled(checked); self.adaptive_zoom_spin.setEnabled(checked)

    def _current_hijri_year(self) -> int:
        try:
            return int(self.hijri_service.estimate(date.today()).year)
        except Exception:
            return 1447

    def _refresh_monthly_year_mode(self) -> None:
        if self.monthly_calendar_type_combo.currentData() == "gregorian":
            self.monthly_year_label.setText("السنة الميلادية")
            self.monthly_year_spin.setRange(1900, 2500)
            if not (1900 <= self.monthly_year_spin.value() <= 2500):
                self.monthly_year_spin.setValue(date.today().year)
        else:
            self.monthly_year_label.setText("السنة الهجرية")
            self.monthly_year_spin.setRange(1300, 1700)
            if not (1300 <= self.monthly_year_spin.value() <= 1700):
                self.monthly_year_spin.setValue(self._current_hijri_year())

    def _refresh_monthly_month_names(self) -> None:
        current_data = self.monthly_month_combo.currentData()
        self.monthly_month_combo.blockSignals(True)
        self.monthly_month_combo.clear()
        month_names = AR_MONTHS_GREGORIAN if self.monthly_calendar_type_combo.currentData() == "gregorian" else AR_MONTHS_HIJRI
        for idx, name in enumerate(month_names, start=1):
            self.monthly_month_combo.addItem(name, idx)
        idx = self.monthly_month_combo.findData(current_data)
        self.monthly_month_combo.setCurrentIndex(max(0, idx))
        self.monthly_month_combo.blockSignals(False)
        self._refresh_monthly_year_mode()

    def _fallback_config(self) -> dict:
        if not self.config_path.exists(): return dict(countries=[])
        return json.loads(self.config_path.read_text(encoding="utf-8"))

    def _load_countries(self) -> None:
        self.country_combo.clear()
        try:
            countries = self.reference_repo.get_countries()
            if countries:
                for country in countries: self.country_combo.addItem(country["name_ar"], country)
                self.status_label.setText("تم تحميل الدول والمدن من MySQL."); self._refresh_cities(); return
            raise RuntimeError("No active countries in database.")
        except Exception as exc:
            cfg = self._fallback_config()
            for country in cfg.get("countries", []): self.country_combo.addItem(country["name_ar"], country)
            self.status_label.setText("تم استخدام ملف JSON الاحتياطي لأن تحميل MySQL تعذر: " + str(exc)); self._refresh_cities()

    def _refresh_cities(self) -> None:
        self.city_combo.clear(); country = self.country_combo.currentData()
        if not country: return
        if isinstance(country, dict) and "id" in country and "country_code" in country:
            for city in self.reference_repo.get_cities_by_country_id(country["id"]): self.city_combo.addItem(city["name_ar"], city)
            return
        for city in country.get("cities", []): self.city_combo.addItem(city["name_ar"], city)

    def _current_location(self) -> Location:
        city = self.city_combo.currentData()
        if not city: raise ValueError("لم يتم اختيار مدينة.")
        return Location(name=city["name_en"], latitude=city["latitude"], longitude=city["longitude"], elevation_meters=city["elevation"], timezone=city["timezone"])

    @staticmethod
    def _weekday_ar(d: date) -> str: return AR_WEEKDAYS[d.weekday()]
    @staticmethod
    def _fmt_dt(value) -> str: return "غير متوفر" if value is None else value.strftime("%Y-%m-%d %H:%M:%S %z")
    @staticmethod
    def _fmt_time(value) -> str: return "" if value is None else value.strftime("%H:%M")
    @staticmethod
    def _fmt_float(value, digits=2, suffix="") -> str: return "غير متوفر" if value is None else f"{value:.{digits}f}{suffix}"
    @staticmethod
    def _fmt_lag(value) -> str:
        if value is None: return "غير متوفر"
        if value <= 0: return "غير منطبق"
        return f"{value:.2f} دقيقة"
    @staticmethod
    def _format_estimated_hijri(value) -> str:
        if value is None: return "غير متوفر"
        try: return f"{value.day} {value.month_name} {value.year} ({value.source})"
        except Exception: return str(value)
    @staticmethod
    def _format_scientific_results(results) -> str:
        lines = ["جدول المعايير العلمية", "", "المعيار | القيمة الخام | الفئة | التفسير", "-" * 80]
        for result in results:
            raw = "غير متوفر" if getattr(result, "raw_value", None) is None else f"{result.raw_value:.4f}"
            lines.append(f"{result.criterion_name} | {raw} | {result.category} | {result.explanation}")
        return "\n".join(lines)

    def _extract_result(self, results, name):
        for result in results:
            if getattr(result, "criterion_name", "") == name: return result
        return None

    def _run_calculation(self) -> None:
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor)); self.calc_button.setEnabled(False); self.latest_button.setEnabled(False)
        try:
            self.status_label.setText("جاري الحساب..."); QApplication.processEvents(); location = self._current_location(); target_date = self.date_edit.date().toPython(); country = self.country_combo.currentData(); profile_code = "JO_OFFICIAL_WORKING"
            if isinstance(country, dict): profile_code = country.get("default_profile_code") or country.get("default_profile") or profile_code
            prayer_times = self.prayer_service.calculate(location, target_date, profile_code=profile_code); estimated_hijri = self.hijri_service.estimate(target_date); next_conjunction = self.conjunction_service.find_next_conjunction(target_date); candidate_evening, candidate_note = self.candidate_service.find_candidate_evening(location, next_conjunction); moon_data, crescent_eval = self.moon_service.calculate(location, candidate_evening, conjunction_dt=next_conjunction); scientific_results = self.visibility_service.evaluate_all(moon_data); odeh_result = self._extract_result(scientific_results, "Odeh"); weekday_label = self._weekday_ar(target_date); candidate_weekday = self._weekday_ar(candidate_evening)
            self.prayer_tab.setPlainText("\n".join([f"اليوم: {weekday_label}", f"التاريخ الميلادي: {target_date.isoformat()}", f"التاريخ الهجري التقديري: {self._format_estimated_hijri(estimated_hijri)}", "", "الصلوات الأساسية", f"الفجر: {self._fmt_dt(prayer_times.fajr)}", f"الشروق: {self._fmt_dt(prayer_times.sunrise)}", f"الظهر: {self._fmt_dt(prayer_times.dhuhr)}", f"العصر: {self._fmt_dt(prayer_times.asr)}", f"المغرب: {self._fmt_dt(prayer_times.maghrib)}", f"العشاء: {self._fmt_dt(prayer_times.isha)}", "", "المواقيت الشرعية الإضافية", f"الإمساك: {self._fmt_dt(prayer_times.imsak)}", f"بداية الضحى: {self._fmt_dt(prayer_times.duha_start)}", f"بداية الزوال: {self._fmt_dt(prayer_times.zawal_start)}", f"نصف الليل الشرعي: {self._fmt_dt(prayer_times.midnight)}", f"بداية الثلث الأخير: {self._fmt_dt(prayer_times.last_third_start)}", f"بداية القيام: {self._fmt_dt(prayer_times.qiyam_start)}", "", "أوقات الكراهة", f"نهاية كراهة ما بعد الشروق: {self._fmt_dt(prayer_times.karaha_after_sunrise_end)}", f"بداية كراهة ما قبل الزوال: {self._fmt_dt(prayer_times.karaha_before_zawal_start)}", f"نهاية كراهة ما قبل الزوال: {self._fmt_dt(prayer_times.karaha_before_zawal_end)}", f"بداية كراهة ما بعد العصر: {self._fmt_dt(prayer_times.karaha_after_asr_start)}", f"نهاية كراهة ما بعد العصر: {self._fmt_dt(prayer_times.karaha_after_asr_end)}", "", f"رمز الملف المعتمد: {prayer_times.profile_code}"]))
            self.hijri_tab.setPlainText("\n".join([f"اليوم: {candidate_weekday}", f"التاريخ المرجعي الأساسي: {target_date.isoformat()} ({weekday_label})", f"التاريخ الهجري التقديري لليوم الأساسي: {self._format_estimated_hijri(estimated_hijri)}", f"الاقتران القادم: {self._fmt_dt(next_conjunction)}", f"أول ليلة مرشحة: {candidate_evening.isoformat()}", f"ملاحظة: {candidate_note}"]))
            self.moon_tab.setPlainText("\n".join([f"الاقتران: {self._fmt_dt(moon_data.conjunction)}", f"غروب الشمس: {self._fmt_dt(moon_data.sunset)}", f"غروب القمر: {self._fmt_dt(moon_data.moonset)}", f"عمر الهلال: {self._fmt_float(moon_data.moon_age_hours, 2, ' ساعة')}", f"الارتفاع: {self._fmt_float(moon_data.altitude_deg, 2, ' درجة')}", f"الاستطالة: {self._fmt_float(moon_data.elongation_deg, 2, ' درجة')}", f"المكث: {self._fmt_lag(moon_data.lag_time_minutes)}"]))
            self.science_tab.setPlainText(self._format_scientific_results(scientific_results)); self.operational_tab.setPlainText("\n".join([f"الحالة الفلكية: {crescent_eval.astronomical_status}", f"حالة المكث: {crescent_eval.mukth_status}", f"حالة الرؤية: {crescent_eval.visibility_status}", f"التقييم التشغيلي: {crescent_eval.jordan_operational_status}", f"الحالة الرسمية: {crescent_eval.official_status}", f"الملخص: {crescent_eval.reason_summary}", f"التفصيل: {crescent_eval.detailed_reasoning}"]))
            self.summary_text.setPlainText("\n".join([f"الدولة: {self.country_combo.currentText()}", f"المدينة: {self.city_combo.currentText()}", f"اليوم: {weekday_label}", f"التاريخ: {target_date.isoformat()}", f"الهجري التقديري: {self._format_estimated_hijri(estimated_hijri)}", f"Odeh: {odeh_result.category if odeh_result else 'غير متوفر'}"])); self.status_label.setText("اكتمل الحساب بنجاح.")
        except Exception as exc:
            self.status_label.setText("حدث خطأ أثناء الحساب."); QMessageBox.critical(self, "خطأ", "تعذر إكمال العملية:\n" + str(exc))
        finally:
            self.calc_button.setEnabled(True); self.latest_button.setEnabled(True); QApplication.restoreOverrideCursor()

    def _estimate_hijri_for_date(self, day: date): return self.hijri_service.estimate(day)
    def _resolve_hijri_month_dates(self, h_year: int, h_month: int, source_code: str):
        if source_code == "official": raise RuntimeError("التقويم الهجري الرسمي للدولة غير متوفر بعد في هذه النسخة.")
        g_year_guess = int((h_year - 1) * 0.970224 + 621.5774); start = date(g_year_guess - 1, 1, 1); end = date(g_year_guess + 1, 12, 31); results = []; current = start
        while current <= end:
            h = self._estimate_hijri_for_date(current)
            if h.year == h_year and h.month == h_month: results.append(current)
            current += timedelta(days=1)
        if not results: raise RuntimeError("تعذر إيجاد أيام هذا الشهر الهجري ضمن المجال المحسوب.")
        return results

    def _generate_monthly_calendar(self) -> None:
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        try:
            location = self._current_location(); country = self.country_combo.currentData(); profile_code = "JO_OFFICIAL_WORKING"
            if isinstance(country, dict): profile_code = country.get("default_profile_code") or country.get("default_profile") or profile_code
            calendar_type = self.monthly_calendar_type_combo.currentData(); source_code = self.monthly_hijri_source_combo.currentData(); year_value = int(self.monthly_year_spin.value()); month_value = int(self.monthly_month_combo.currentData())
            if calendar_type == "gregorian":
                day_count = calendar.monthrange(year_value, month_value)[1]; date_list = [date(year_value, month_value, d) for d in range(1, day_count + 1)]; calendar_title = f"تقويم {AR_MONTHS_GREGORIAN[month_value - 1]} {year_value} (ميلادي)"
            else:
                date_list = self._resolve_hijri_month_dates(year_value, month_value, source_code); source_label = "حسابي" if source_code == "calculated" else "رسمي"; calendar_title = f"تقويم {AR_MONTHS_HIJRI[month_value - 1]} {year_value} ({source_label})"
            self.monthly_rows = []; self.monthly_table.setRowCount(len(date_list))
            for row_idx, current_date in enumerate(date_list):
                prayers = self.prayer_service.calculate(location, current_date, profile_code=profile_code); hijri = self._estimate_hijri_for_date(current_date)
                row_values = [self._weekday_ar(current_date), current_date.isoformat(), self._format_estimated_hijri(hijri), self._fmt_time(prayers.fajr), self._fmt_time(prayers.sunrise), self._fmt_time(prayers.dhuhr), self._fmt_time(prayers.asr), self._fmt_time(prayers.maghrib), self._fmt_time(prayers.isha)]
                self.monthly_rows.append(row_values)
                for col_idx, value in enumerate(row_values): self.monthly_table.setItem(row_idx, col_idx, QTableWidgetItem(value))
            self.monthly_table.resizeColumnsToContents(); self.monthly_info_text.setPlainText("\n".join([calendar_title, f"الدولة: {self.country_combo.currentText()}", f"المدينة: {self.city_combo.currentText()}", f"عدد الأيام المعروضة: {len(date_list)}", f"رمز ملف المواقيت: {profile_code}"]))
            self.tabs.setCurrentWidget(self.monthly_tab); self.status_label.setText("تم توليد التقويم الشهري بنجاح.")
        except Exception as exc:
            QMessageBox.critical(self, "خطأ", "تعذر توليد التقويم الشهري:\n" + str(exc)); self.status_label.setText("فشل توليد التقويم الشهري.")
        finally:
            QApplication.restoreOverrideCursor()

    def _copy_monthly_table(self) -> None:
        if not self.monthly_rows: QMessageBox.information(self, "التقويم الشهري", "لا توجد بيانات شهرية لنسخها."); return
        headers = [self.monthly_table.horizontalHeaderItem(i).text() for i in range(self.monthly_table.columnCount())]; lines = ["\t".join(headers)] + ["\t".join(row) for row in self.monthly_rows]; QApplication.clipboard().setText("\n".join(lines)); self.status_label.setText("تم نسخ الجدول إلى الحافظة.")

    def _export_monthly_table(self) -> None:
        if not self.monthly_rows: QMessageBox.information(self, "التقويم الشهري", "لا توجد بيانات شهرية لتصديرها."); return
        if Workbook is None: QMessageBox.warning(self, "التقويم الشهري", "مكتبة openpyxl غير متوفرة، لذلك لا يمكن التصدير إلى Excel في هذه البيئة."); return
        filepath, _ = QFileDialog.getSaveFileName(self, "تصدير التقويم الشهري", "monthly_prayer_calendar.xlsx", "Excel Files (*.xlsx)")
        if not filepath: return
        wb = Workbook(); ws = wb.active; ws.title = "Prayer Calendar"; headers = [self.monthly_table.horizontalHeaderItem(i).text() for i in range(self.monthly_table.columnCount())]; ws.append(headers)
        for row in self.monthly_rows: ws.append(row)
        wb.save(filepath); self.status_label.setText("تم تصدير التقويم الشهري إلى Excel.")

    def _resolve_map_target_date(self):
        base_date = self.date_edit.date().toPython()
        if self.map_date_manual_radio.isChecked(): return self.map_date_edit.date().toPython(), "تاريخ يدوي"
        try:
            next_conjunction = self.conjunction_service.find_next_conjunction(base_date); anchor_location = self._current_location(); candidate_evening, _ = self.candidate_service.find_candidate_evening(anchor_location, next_conjunction); return candidate_evening, "أول مساء صالح بعد الاقتران"
        except Exception:
            return base_date, "تعذر تحديد أول مساء صالح بعد الاقتران؛ تم الرجوع إلى التاريخ الأساسي"

    def _start_generate_visibility_map(self) -> None:
        if self.map_thread is not None: QMessageBox.information(self, "الخريطة", "توليد الخريطة ما زال يعمل."); return
        resolution = self.map_resolution_combo.currentData(); resolution = float(self.map_resolution_custom.value()) if resolution == "custom" else resolution
        if float(resolution) <= 0.5:
            reply = QMessageBox.warning(self, "تحذير", "هذه الدقة قد تستغرق وقتًا طويلًا جدًا. هل تريد المتابعة؟", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes: return
        target_date, date_mode_text = self._resolve_map_target_date(); criterion = str(self.map_criterion_combo.currentData()); basemap = str(self.map_style_combo.currentData()); adaptive_enabled = self.adaptive_checkbox.isChecked(); adaptive_resolution = float(self.adaptive_resolution_spin.value()); adaptive_zoom = int(self.adaptive_zoom_spin.value())
        self.progress_bar.setValue(0); self.progress_bar.show(); self.progress_label.setText("0%"); self.progress_label.show(); self.status_label.setText("بدء توليد الخريطة..."); self.generate_map_button.setEnabled(False); self.cancel_map_button.setEnabled(True); self.tabs.setCurrentWidget(self.map_settings_tab)
        self.map_thread = QThread(self); self.map_worker = MapGenerationWorker(generator=self.map_generator, target_date=target_date, resolution_deg=float(resolution), criterion_name=criterion, adaptive_enabled=adaptive_enabled, adaptive_resolution_deg=adaptive_resolution, adaptive_zoom_threshold=adaptive_zoom, basemap=basemap, date_mode_text=date_mode_text); self.map_worker.moveToThread(self.map_thread); self.map_thread.started.connect(self.map_worker.run); self.map_worker.progress_changed.connect(self._on_map_progress); self.map_worker.finished.connect(self._on_map_finished); self.map_worker.failed.connect(self._on_map_failed); self.map_worker.cancelled.connect(self._on_map_cancelled); self.map_worker.finished.connect(self.map_thread.quit); self.map_worker.failed.connect(self.map_thread.quit); self.map_worker.cancelled.connect(self.map_thread.quit); self.map_thread.finished.connect(self._cleanup_map_thread); self.map_thread.start()

    def _cancel_map_generation(self) -> None:
        if self.map_worker is not None: self.map_worker.request_cancel(); self.status_label.setText("جاري إلغاء التوليد..."); self.cancel_map_button.setEnabled(False)

    def _on_map_progress(self, percent: int, message: str) -> None:
        self.progress_bar.setValue(percent); self.progress_label.setText(str(percent) + "%"); self.status_label.setText(message)

    def _on_map_finished(self, feature_collection: dict, stats: dict, basemap: str) -> None:
        self.last_map_feature_collection = feature_collection; self.last_map_stats = stats; index = self.result_basemap_combo.findData(basemap)
        if index >= 0: self.result_basemap_combo.setCurrentIndex(index)
        self.map_view.render_feature_collection(feature_collection, basemap=basemap); self.result_map_note.setText("الخريطة المعروضة قابلة لتبديل نوع الخلفية بدون إعادة حساب.")
        self.map_info_text.setPlainText("\n".join(["تاريخ الخريطة الفعلي: " + str(stats["target_date"]), "طريقة تحديد التاريخ: " + str(stats["date_mode_text"]), "الدقة الأساسية: " + str(stats["resolution_deg"]) + "°", "عدد الخلايا: " + str(stats["point_count"]), "المعيار: " + str(stats["criterion_name"]), "نوع الخريطة عند التوليد: " + basemap, "الدقة التكيفية: " + ("مفعلة" if stats["adaptive_enabled"] else "غير مفعلة"), "الدقة المحلية: " + str(stats["adaptive_resolution_deg"]) + "°", "Zoom التفعيل: " + str(stats["adaptive_zoom_threshold"]), "", "شرح الألوان:", "الأخضر = مرئي", "الأصفر = مرئي بمساعدة بصرية", "الأحمر = غير مرئي", "الأزرق = فوق الحد", "البني = تحت الحد", "الرمادي = غير محدد"]))
        self.progress_bar.hide(); self.progress_label.hide(); self.progress_bar.setValue(100); self.progress_label.setText("100%"); self.status_label.setText("اكتمل توليد الخريطة بنجاح."); self.generate_map_button.setEnabled(True); self.cancel_map_button.setEnabled(False); self.tabs.setCurrentWidget(self.map_result_tab)

    def _on_map_failed(self, error_text: str) -> None:
        self.progress_bar.hide(); self.progress_label.hide(); self.progress_bar.setValue(0); self.progress_label.setText("0%"); self.status_label.setText("فشل توليد الخريطة."); self.generate_map_button.setEnabled(True); self.cancel_map_button.setEnabled(False); QMessageBox.critical(self, "خطأ", "تعذر توليد الخريطة:\n" + error_text)

    def _on_map_cancelled(self) -> None:
        self.progress_bar.hide(); self.progress_label.hide(); self.progress_bar.setValue(0); self.progress_label.setText("0%"); self.status_label.setText("تم إلغاء توليد الخريطة."); self.generate_map_button.setEnabled(True); self.cancel_map_button.setEnabled(False)

    def _cleanup_map_thread(self) -> None:
        if self.map_worker is not None: self.map_worker.deleteLater()
        if self.map_thread is not None: self.map_thread.deleteLater()
        self.map_worker = None; self.map_thread = None

    def _rerender_last_map_with_new_basemap(self) -> None:
        if self.last_map_feature_collection is None: return
        basemap = str(self.result_basemap_combo.currentData()); self.map_view.render_feature_collection(self.last_map_feature_collection, basemap=basemap); self.status_label.setText("تم تغيير نوع الخريطة بدون إعادة الحساب.")

    def _fmt_saved_value(self, value) -> str:
        return "غير متوفر" if value is None else str(value)

    def _restore_saved_run(self, summary: dict, details: dict) -> None:
        run = details.get("run") or {}
        prayer = details.get("prayer_times") or {}
        moon = details.get("moon_data") or {}
        visibility = details.get("visibility") or []

        greg_date = str(run.get("gregorian_date", ""))
        weekday_text = ""
        try:
            weekday_text = self._weekday_ar(datetime.strptime(greg_date, "%Y-%m-%d").date())
        except Exception:
            pass

        self.prayer_tab.setPlainText("\n".join([
            "المواقيت الأساسية من التشغيل المحفوظ",
            f"اليوم: {weekday_text}" if weekday_text else "اليوم: غير متوفر",
            f"التاريخ الميلادي: {greg_date}",
            f"الفجر: {self._fmt_saved_value(prayer.get('fajr'))}",
            f"الشروق: {self._fmt_saved_value(prayer.get('sunrise'))}",
            f"الظهر: {self._fmt_saved_value(prayer.get('dhuhr'))}",
            f"العصر: {self._fmt_saved_value(prayer.get('asr'))}",
            f"المغرب: {self._fmt_saved_value(prayer.get('maghrib'))}",
            f"العشاء: {self._fmt_saved_value(prayer.get('isha'))}",
        ]))
        self.hijri_tab.setPlainText("\n".join([
            "تفاصيل اليوم المخزن",
            f"اليوم: {weekday_text}" if weekday_text else "اليوم: غير متوفر",
            f"التاريخ الميلادي: {greg_date}",
            "ملاحظة: هذا العرض مسترجع من الخادم بناءً على التشغيل المحفوظ.",
        ]))
        self.moon_tab.setPlainText("\n".join([
            "بيانات الهلال من التشغيل المحفوظ",
            f"عمر الهلال: {self._fmt_saved_value(moon.get('moon_age_hours'))}",
            f"الارتفاع: {self._fmt_saved_value(moon.get('altitude_deg'))}",
            f"الاستطالة: {self._fmt_saved_value(moon.get('elongation_deg'))}",
            f"المكث: {self._fmt_saved_value(moon.get('lag_time_minutes'))}",
        ]))
        vis_lines = ["المعايير العلمية من التشغيل المحفوظ", ""]
        op_lines = ["النتائج التشغيلية من التشغيل المحفوظ", ""]
        for row in visibility:
            line = f"{row.get('criterion_name')} | {row.get('category')} | {row.get('explanation')}"
            if row.get("criterion_name") == "JordanOperational":
                op_lines.append(line)
            else:
                vis_lines.append(line)
        self.science_tab.setPlainText("\n".join(vis_lines))
        self.operational_tab.setPlainText("\n".join(op_lines))
        self.summary_text.setPlainText("\n".join([
            "تم استرجاع تشغيل محفوظ",
            f"رقم التشغيل: {summary.get('id')}",
            f"المدينة: {summary.get('city')}",
            f"التاريخ: {greg_date}",
            f"وقت الإدخال: {summary.get('created_at')}",
        ]))
        self.storage_tab.setPlainText("\n".join([
            "التشغيل المحفوظ المسترجع",
            f"رقم التشغيل: {summary.get('id')}",
            f"المدينة: {summary.get('city')}",
            f"التاريخ: {greg_date}",
            f"وقت الإدخال: {summary.get('created_at')}",
            "",
            "يمكنك الآن مراجعة التبويبات المختلفة لعرض البيانات المسترجعة.",
        ]))
        self.tabs.setCurrentWidget(self.storage_tab)
        self.status_label.setText("تم استرجاع التشغيل المحفوظ بنجاح.")

    def _show_latest_saved_run(self) -> None:
        if ResultsQueryRepository is None:
            self.storage_tab.setPlainText("ResultsQueryRepository غير متوفر في المشروع الحالي.")
            self.tabs.setCurrentWidget(self.storage_tab)
            return
        try:
            repo = ResultsQueryRepository()
            dialog = SavedRunsBrowserDialog(repo, self)
            if dialog.exec() != QDialog.Accepted or dialog.selected_run is None:
                return
            selected = dialog.selected_run
            details = repo.get_run(selected["id"])
            self._restore_saved_run(selected, details)
        except Exception as exc:
            QMessageBox.critical(self, "خطأ", "تعذر استعراض أو استرجاع التشغيلات المحفوظة:\n" + str(exc))


def main() -> int:
    app = QApplication(sys.argv); app.setLayoutDirection(Qt.RightToLeft); window = ArabicMainWindow(); window.show(); return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
