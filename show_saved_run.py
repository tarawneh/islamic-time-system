
import argparse
from results_query_repository import ResultsQueryRepository

parser = argparse.ArgumentParser()
parser.add_argument("--run-id", type=int, required=True)

args = parser.parse_args()

repo = ResultsQueryRepository()
data = repo.get_run(args.run_id)

print("Calculation Run")
print(data["run"])
print()

print("Prayer Times")
print(data["prayer_times"])
print()

print("Moon Data")
print(data["moon_data"])
print()

print("Visibility Results")
for v in data["visibility"]:
    print(v)
