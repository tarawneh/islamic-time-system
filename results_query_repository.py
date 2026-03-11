# ============================================================================
# File Name   : results_query_repository.py
# Version     : 0.7.4
# Author      : Dr. Rami Tarawneh
# Company     : 7th Layer
# Project     : Islamic Time System
# Description : Query stored calculation results from MySQL, including calendar-
#               style browsing by month and by specific day.
# License     : GNU General Public License v3.0 or later
# ============================================================================

from __future__ import annotations
from mysql_client import get_connection

class ResultsQueryRepository:
    def get_latest_run(self):
        conn = get_connection(True)
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT *
            FROM calculation_runs
            ORDER BY id DESC
            LIMIT 1
        """)
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row

    def get_days_with_runs_for_month(self, year: int, month: int):
        conn = get_connection(True)
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT DISTINCT DAY(gregorian_date) AS run_day
            FROM calculation_runs
            WHERE YEAR(gregorian_date) = %s
              AND MONTH(gregorian_date) = %s
            ORDER BY run_day
            """,
            (year, month),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [int(r["run_day"]) for r in rows]

    def get_runs_for_day(self, gregorian_date_iso: str):
        conn = get_connection(True)
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT *
            FROM calculation_runs
            WHERE gregorian_date = %s
            ORDER BY created_at DESC, id DESC
            """,
            (gregorian_date_iso,),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

    def get_run(self, run_id):
        conn = get_connection(True)
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM calculation_runs WHERE id=%s", (run_id,))
        run = cur.fetchone()
        cur.execute("SELECT * FROM prayer_times WHERE run_id=%s", (run_id,))
        prayer = cur.fetchone()
        cur.execute("SELECT * FROM moon_data WHERE run_id=%s", (run_id,))
        moon = cur.fetchone()
        cur.execute("SELECT * FROM visibility_results WHERE run_id=%s", (run_id,))
        visibility = cur.fetchall()
        cur.close()
        conn.close()
        return {"run": run, "prayer_times": prayer, "moon_data": moon, "visibility": visibility}
