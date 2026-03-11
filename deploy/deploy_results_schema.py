# ============================================================================
# File Name   : deploy_results_schema.py
# Title       : MySQL Results Schema Deployer
# Version     : 0.5.2
# Build Date  : 2026-03-09 21:11:37 UTC
# Author      : Dr. Rami Tarawneh
# Company     : 7th Layer
# Project     : Islamic Time System
# Description : Deploys the results storage schema to the configured MySQL
#               database from the local machine. This script reads connection
#               settings from environment variables loaded via .env, ensures
#               that the target database exists, then executes the SQL file
#               results_schema.sql statement by statement.
# License     : GNU General Public License v3.0 or later
#
# GNU General Public License Notice:
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# ============================================================================
from __future__ import annotations

from pathlib import Path
import sys

from mysql_client import ensure_database_exists, execute_sql_script, test_connection
from mysql_config import load_mysql_config


def main() -> int:
    cfg = load_mysql_config()
    schema_path = Path("results_schema.sql")

    if not schema_path.exists():
        print("ERROR: results_schema.sql was not found in the current folder.")
        print("Place deploy_results_schema.py in the same folder as results_schema.sql")
        print("or run the script from that folder.")
        return 1

    print("Testing MySQL connection...")
    try:
        version, hostname = test_connection()
    except Exception as exc:
        print(f"ERROR: MySQL connection failed: {exc}")
        return 2

    print("Connected successfully.")
    print(f"Server version: {version}")
    print(f"Server hostname: {hostname}")
    print(f"Target database: {cfg.database}")
    print()

    try:
        ensure_database_exists()
        print(f"Database ensured: {cfg.database}")
    except Exception as exc:
        print(f"ERROR: Failed to ensure database exists: {exc}")
        return 3

    try:
        execute_sql_script(schema_path)
        print("Results schema deployed successfully.")
        return 0
    except Exception as exc:
        print(f"ERROR: Failed to deploy results schema: {exc}")
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
