# ============================================================================
# File Name   : reference_repository.py
# Version     : 0.6.1
# Build Date  : 2026-03-09 22:06:42 UTC
# Author      : Dr. Rami Tarawneh
# Company     : 7th Layer
# Description : Reads countries and cities from MySQL for the Arabic GUI.
# ============================================================================

from mysql_client import get_connection


class ReferenceRepository:
    def get_countries(self):
        conn = get_connection(True)
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id, country_code, name_ar, name_en, default_profile_code
            FROM countries
            WHERE is_active = 1
            ORDER BY display_order, name_ar
            """
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

    def get_cities_by_country_id(self, country_id):
        conn = get_connection(True)
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id, city_code, name_ar, name_en, latitude, longitude, elevation, timezone
            FROM cities
            WHERE is_active = 1 AND country_id = %s
            ORDER BY display_order, name_ar
            """,
            (country_id,),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
