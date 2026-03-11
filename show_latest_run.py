
from results_query_repository import ResultsQueryRepository

repo = ResultsQueryRepository()

run = repo.get_latest_run()

if not run:
    print("No runs found in database.")
else:
    print("Latest Run")
    print(run)
