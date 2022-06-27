import pandas
import string

results_raw = pandas.read_csv("final-precinct-results.csv")
for ignore in ("Times Counted", "Times Over Voted", "Times Under Voted", "Write-in", "Registered Voters"):
    results_raw = results_raw[results_raw["CounterType"] != ignore]

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
        #j = string.ascii_uppercase[len(options[race])]
        j = option.replace(".", "_")
        options[race].append(option)
    i = race.replace(".", "_")
    new_col = str(i) + "." + j
    #print(new_col, race, option)
    new_cols.append(new_col)

results = results.reset_index()
s = results["Precinct"].str.split(" ", n=1, expand=True)
results = results[s[0] == "SEA"]
results = results.dropna(axis=1, how="any")
g = results.groupby(axis=1, level=0).count()
new_cols = ["Precinct"]
for c in g:
    if c == "Precinct":
        continue
    # Only one option
    if (g[c] < 2).all():
        continue
    a, b = results[c].columns
    same = results[c][a] > results[c][b]
    loser_precincts = same.value_counts().min()
    if loser_precincts > 100 and loser_precincts != len(results):
        print(c, loser_precincts)
        new_cols.append(c)

results = results[new_cols]
print(results.sum())
print(results.columns.get_level_values(1))
results.to_csv("elections/202111.csv", index=False)
