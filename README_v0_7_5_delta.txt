Islamic Time System
Delta Notes for Version 0.7.5
Build Date: 2026-03-11 00:00:00 UTC
Author: Dr. Rami Tarawneh
Company: 7th Layer

Summary
-------
This version starts the first scientific correction pass for crescent visibility.
The work focuses on consistency of reference frames and sunset-based lunar metrics.

Files Updated
-------------
1. core/interfaces/astronomy_engine.py
2. core/models/moon_data.py
3. modules/astronomy/basic_engine.py
4. modules/moon/service.py
5. modules/moon_visibility/odeh.py
6. modules/moon_visibility/service.py

Scientific Changes
------------------
1. Added explicit sunset-based methods to the astronomy engine interface:
   - solar altitude at sunset
   - ARCV at sunset
   - crescent width at sunset

2. Standardized rise/set event definitions in the astronomy engine:
   - Sun events use -0.833 degrees.
   - Moon events use -0.727 degrees.

3. Kept conjunction geocentric by design and documented that choice.

4. Unified sunset-based lunar metrics under one apparent topocentric observer frame.

5. Expanded MoonData to preserve:
   - conjunction reference label
   - solar altitude at sunset
   - ARCV
   - crescent width

6. Updated the scientific visibility layer so Odeh receives direct ARCV and W inputs
   when available instead of reconstructing them indirectly.

Engineering Notes
-----------------
1. The edited files now contain heavier inline documentation to make scientific intent
   and implementation decisions easier to read during future maintenance.

2. Backward-compatible fallbacks were kept where practical so the rest of the project
   can migrate gradually.

3. This version is a foundation pass. It does not yet add Schaefer, sky brightness,
   probability models, or adaptive map refinement.
