INSERT INTO prayer_profiles (
    profile_code, profile_name_ar, profile_name_en, country_code, authority_name,
    source_type, source_reference, verification_status, notes
) VALUES (
    'JO_OFFICIAL_WORKING', 'الملف الأردني التشغيلي للمواقيت',
    'Jordan Official Working Prayer Profile', 'JO',
    'Jordan official prayer timetable working basis',
    'official_working',
    'Working engineering profile pending full technical extraction from official timetable source',
    'pending',
    'Working Jordan profile used for application development until a fully extracted official technical source is entered'
)
ON DUPLICATE KEY UPDATE
profile_name_ar = VALUES(profile_name_ar),
profile_name_en = VALUES(profile_name_en),
country_code = VALUES(country_code),
authority_name = VALUES(authority_name),
source_type = VALUES(source_type),
source_reference = VALUES(source_reference),
verification_status = VALUES(verification_status),
notes = VALUES(notes);

INSERT INTO prayer_profile_rules (
    profile_id, fajr_angle_deg, isha_angle_deg, sunrise_altitude_deg, sunset_altitude_deg,
    asr_method, imsak_offset_minutes, duha_offset_minutes, zawal_offset_minutes,
    midnight_method, qiyam_method, karaha_after_sunrise_minutes, karaha_before_zawal_minutes,
    karaha_after_asr_to_maghrib, is_active
)
SELECT p.id, 18.000, 17.000, -0.833, -0.833, 'SHAFII', 10, 15, 5,
       'SUNSET_TO_FAJR', 'LAST_THIRD', 15, 5, 1, 1
FROM prayer_profiles p
WHERE p.profile_code = 'JO_OFFICIAL_WORKING'
ON DUPLICATE KEY UPDATE
fajr_angle_deg = VALUES(fajr_angle_deg),
isha_angle_deg = VALUES(isha_angle_deg),
sunrise_altitude_deg = VALUES(sunrise_altitude_deg),
sunset_altitude_deg = VALUES(sunset_altitude_deg),
asr_method = VALUES(asr_method),
imsak_offset_minutes = VALUES(imsak_offset_minutes),
duha_offset_minutes = VALUES(duha_offset_minutes),
zawal_offset_minutes = VALUES(zawal_offset_minutes),
midnight_method = VALUES(midnight_method),
qiyam_method = VALUES(qiyam_method),
karaha_after_sunrise_minutes = VALUES(karaha_after_sunrise_minutes),
karaha_before_zawal_minutes = VALUES(karaha_before_zawal_minutes),
karaha_after_asr_to_maghrib = VALUES(karaha_after_asr_to_maghrib),
is_active = VALUES(is_active);

UPDATE countries SET default_profile_code = 'JO_OFFICIAL_WORKING' WHERE country_code = 'JO';
