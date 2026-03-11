from mysql_client import get_connection

class PrayerProfileRepository:
    def get_rules_by_profile_code(self, profile_code):
        conn = get_connection(True)
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT p.profile_code, p.profile_name_ar, p.profile_name_en, p.country_code,
                   p.verification_status, r.fajr_angle_deg, r.isha_angle_deg,
                   r.sunrise_altitude_deg, r.sunset_altitude_deg, r.asr_method,
                   r.imsak_offset_minutes, r.duha_offset_minutes, r.zawal_offset_minutes,
                   r.midnight_method, r.qiyam_method, r.karaha_after_sunrise_minutes,
                   r.karaha_before_zawal_minutes, r.karaha_after_asr_to_maghrib
            FROM prayer_profiles p
            JOIN prayer_profile_rules r ON r.profile_id = p.id
            WHERE p.is_active = 1 AND r.is_active = 1 AND p.profile_code = %s
            LIMIT 1
            """,
            (profile_code,),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row
