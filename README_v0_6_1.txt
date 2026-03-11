V0.6.1 GUI + MYSQL COUNTRIES/CITIES

Files:
- countries_cities_schema.sql
- countries_cities_seed.sql
- deploy_countries_cities.py
- modules/reference/reference_repository.py
- gui_main_ar.py
- gui/gui_config_ar.json
- requirements_gui.txt

Step 1:
Deploy countries and cities tables:
  python deploy_countries_cities.py

Step 2:
Place reference_repository.py under:
  modules/reference/reference_repository.py

Step 3:
Replace gui_main_ar.py with this version.

Step 4:
Run the GUI:
  python gui_main_ar.py

Behavior:
- The GUI first tries to load countries and cities from MySQL.
- If MySQL loading fails, it falls back to gui/gui_config_ar.json.
