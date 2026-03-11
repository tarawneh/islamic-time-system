# Author: Dr. Rami Tarawneh
# Company: 7th Layer
# Version: 0.6.1
# Build: 2026-03-09 22:06:42 UTC

from pathlib import Path
from mysql_client import ensure_database_exists, execute_sql_script, test_connection
from mysql_config import load_mysql_config

def main():
    cfg = load_mysql_config()
    print("Testing MySQL connection...")
    version, hostname = test_connection()
    print("Connected successfully.")
    print(f"Server version: {version}")
    print(f"Server hostname: {hostname}")
    print(f"Target database: {cfg.database}")
    print()

    ensure_database_exists()
    print(f"Database ensured: {cfg.database}")

    for sql_name in ("countries_cities_schema.sql", "countries_cities_seed.sql"):
        path = Path(sql_name)
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {sql_name}")
        execute_sql_script(path)
        print(f"Executed: {sql_name}")

    print("Countries and cities deployed successfully.")

if __name__ == "__main__":
    main()
