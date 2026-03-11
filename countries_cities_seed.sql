
INSERT INTO countries (country_code, name_ar, name_en, default_profile_code, is_active, display_order)
VALUES ('JO', 'الأردن', 'Jordan', 'JO_OFFICIAL', 1, 1)
ON DUPLICATE KEY UPDATE
name_ar = VALUES(name_ar),
name_en = VALUES(name_en),
default_profile_code = VALUES(default_profile_code),
is_active = VALUES(is_active),
display_order = VALUES(display_order);

INSERT INTO cities (country_id, city_code, name_ar, name_en, latitude, longitude, elevation, timezone, is_active, display_order)
SELECT c.id, 'AMMAN', 'عمّان', 'Amman', 31.9539, 35.9106, 757, 'Asia/Amman', 1, 1
FROM countries c
WHERE c.country_code = 'JO'
ON DUPLICATE KEY UPDATE
name_ar = VALUES(name_ar), latitude = VALUES(latitude), longitude = VALUES(longitude),
elevation = VALUES(elevation), timezone = VALUES(timezone), is_active = VALUES(is_active), display_order = VALUES(display_order);

INSERT INTO cities (country_id, city_code, name_ar, name_en, latitude, longitude, elevation, timezone, is_active, display_order)
SELECT c.id, 'IRBID', 'إربد', 'Irbid', 32.5556, 35.8500, 620, 'Asia/Amman', 1, 2
FROM countries c
WHERE c.country_code = 'JO'
ON DUPLICATE KEY UPDATE
name_ar = VALUES(name_ar), latitude = VALUES(latitude), longitude = VALUES(longitude),
elevation = VALUES(elevation), timezone = VALUES(timezone), is_active = VALUES(is_active), display_order = VALUES(display_order);

INSERT INTO cities (country_id, city_code, name_ar, name_en, latitude, longitude, elevation, timezone, is_active, display_order)
SELECT c.id, 'ZARQA', 'الزرقاء', 'Zarqa', 32.0728, 36.0880, 619, 'Asia/Amman', 1, 3
FROM countries c
WHERE c.country_code = 'JO'
ON DUPLICATE KEY UPDATE
name_ar = VALUES(name_ar), latitude = VALUES(latitude), longitude = VALUES(longitude),
elevation = VALUES(elevation), timezone = VALUES(timezone), is_active = VALUES(is_active), display_order = VALUES(display_order);

INSERT INTO cities (country_id, city_code, name_ar, name_en, latitude, longitude, elevation, timezone, is_active, display_order)
SELECT c.id, 'KARAK', 'الكرك', 'Karak', 31.1854, 35.7048, 930, 'Asia/Amman', 1, 4
FROM countries c
WHERE c.country_code = 'JO'
ON DUPLICATE KEY UPDATE
name_ar = VALUES(name_ar), latitude = VALUES(latitude), longitude = VALUES(longitude),
elevation = VALUES(elevation), timezone = VALUES(timezone), is_active = VALUES(is_active), display_order = VALUES(display_order);

INSERT INTO cities (country_id, city_code, name_ar, name_en, latitude, longitude, elevation, timezone, is_active, display_order)
SELECT c.id, 'AQABA', 'العقبة', 'Aqaba', 29.5321, 35.0063, 6, 'Asia/Amman', 1, 5
FROM countries c
WHERE c.country_code = 'JO'
ON DUPLICATE KEY UPDATE
name_ar = VALUES(name_ar), latitude = VALUES(latitude), longitude = VALUES(longitude),
elevation = VALUES(elevation), timezone = VALUES(timezone), is_active = VALUES(is_active), display_order = VALUES(display_order);
