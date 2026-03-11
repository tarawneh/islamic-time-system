
# Author: Dr. Rami Tarawneh
# Company: 7th Layer
# Version: 0.5.1
# Build: 2026-03-09 21:06:22 UTC

from mysql_client import get_connection

class ResultsRepository:

    def create_run(self, city, lat, lon, gdate):
        conn = get_connection(True)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO calculation_runs(city, latitude, longitude, gregorian_date) VALUES (%s,%s,%s,%s)",
            (city, lat, lon, gdate)
        )
        run_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()
        return run_id

    def insert_prayer_times(self, run_id, data):
        conn = get_connection(True)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO prayer_times VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (
                run_id,
                data["fajr"],
                data["sunrise"],
                data["dhuhr"],
                data["asr"],
                data["maghrib"],
                data["isha"]
            )
        )
        conn.commit()
        cur.close()
        conn.close()

    def insert_moon_data(self, run_id, moon):
        conn = get_connection(True)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO moon_data VALUES (%s,%s,%s,%s,%s)",
            (
                run_id,
                moon["age"],
                moon["altitude"],
                moon["elongation"],
                moon["lag"]
            )
        )
        conn.commit()
        cur.close()
        conn.close()

    def insert_visibility(self, run_id, result):
        conn = get_connection(True)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO visibility_results VALUES (%s,%s,%s,%s,%s)",
            (
                run_id,
                result["criterion"],
                result["value"],
                result["category"],
                result["explanation"]
            )
        )
        conn.commit()
        cur.close()
        conn.close()
