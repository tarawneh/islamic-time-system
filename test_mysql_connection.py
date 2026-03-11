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
    print()
    ensure_database_exists()
    print(f"Database ensured: {cfg.database}")
    schema_path = Path("official_layer_schema.sql")
    if schema_path.exists():
        execute_sql_script(schema_path)
        print("Official Layer schema deployed successfully.")
    else:
        print("Schema file not found; connection test completed without deployment.")

if __name__ == "__main__":
    main()
