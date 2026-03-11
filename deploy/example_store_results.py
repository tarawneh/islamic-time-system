
from results_repository import ResultsRepository

repo = ResultsRepository()

run_id = repo.create_run("Amman",31.95,35.93,"2026-03-09")

repo.insert_prayer_times(run_id,{
"fajr":"2026-03-09 05:33:32",
"sunrise":"2026-03-09 06:55:32",
"dhuhr":"2026-03-09 12:47:05",
"asr":"2026-03-09 16:25:05",
"maghrib":"2026-03-09 18:38:39",
"isha":"2026-03-09 20:00:39"
})

repo.insert_moon_data(run_id,{
"age":14.37,
"altitude":6.55,
"elongation":7.23,
"lag":35.13
})

repo.insert_visibility(run_id,{
"criterion":"Odeh",
"value":0.9873,
"category":"C",
"explanation":"Visible by optical aid"
})

print("Results stored successfully")
