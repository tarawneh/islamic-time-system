Delta package for v0.7.4.

Replace:
- gui_main_ar.py
- results_query_repository.py

What changed:
1) Added a saved-runs browser dialog with calendar highlighting for days that contain stored runs.
2) Clicking the browse button now opens the calendar, then lists all runs for the selected day.
3) Selecting a run restores its stored data into the interface tabs.
4) Fixed Hijri-year handling in the monthly calendar:
   - Gregorian mode uses Gregorian year values.
   - Hijri mode relabels and resets the year selector to Hijri values.
