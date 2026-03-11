Delta package for v0.7.2.

Replace:
- gui_main_ar.py
- modules/maps/leaflet_map_view.py
- modules/maps/visibility_map_generator.py
- modules/maps/map_generation_worker.py

What changed:
1) Map settings now live in a dedicated tab.
2) Map result now lives in a separate tab with a much larger display area.
3) Basemap can be changed after generation without recalculation.
4) Computed values are drawn as semi-transparent rectangular cells instead of points.
