import pandas
import string

results_raw = pandas.read_csv("final-precinct-results.csv")
for ignore in ("Times Counted", "Times Over Voted", "Times Under Voted", "Write-in"):
    results_raw = results_raw[results_raw["CounterType"] != ignore]
print(results_raw)

results = results_raw.pivot(index="Precinct", columns=["Race", "CounterType"], values="SumOfCount")


races = []
options = {}
new_cols = []
for race, option in zip(results.columns.get_level_values(0), results.columns.get_level_values(1)):
    if race not in races:
        races.append(race)
        options[race] = []
    i = races.index(race)
    if option == "Registered Voters":
        j = "RV"
    else:
        j = string.ascii_uppercase[len(options[race])]
        options[race].append(option)
    new_col = str(i) + "." + j
    print(new_col, race, option)
    new_cols.append(new_col)

results.columns = new_cols
print(results)
results.to_csv("election/202111.csv")
