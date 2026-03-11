V0.5.2 AUTO-SAVE TO MYSQL

Files in this package:
- main.py
- modules/storage/results_persistence_service.py

Required existing files:
- mysql_config.py
- mysql_client.py
- results_repository.py
- .env
- All current Islamic Time System calculation modules

Installation:
1. Replace main.py with the version in this package.
2. Add:
   modules/storage/results_persistence_service.py
3. Make sure these files are available in your project root:
   - results_repository.py
   - mysql_client.py
   - mysql_config.py
   - .env
4. Run normally:
   python main.py --city Amman --date 2026-03-09

Optional:
- To skip saving for a single run:
  python main.py --city Amman --date 2026-03-09 --no-save

What gets saved:
- calculation_runs
- prayer_times
- moon_data
- visibility_results
