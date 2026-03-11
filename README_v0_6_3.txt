V0.6.3 visibility models

Files:
- modules/moon_visibility/models.py
- modules/moon_visibility/yallop.py
- modules/moon_visibility/danjon.py
- modules/moon_visibility/service.py

Notes:
- service.py preserves evaluate() for backward compatibility with the existing GUI and main.py
- new evaluate_all(moon_data) returns Odeh + Yallop + Danjon
