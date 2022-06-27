# This script was used to filter the blocks from the block20 redistricting data (too big for github)
# for washington to seattle. Seattle was defined by existing districts plus a polygon to bridge the
# ship canal.

import geopandas
import pathlib
import matplotlib.pyplot as plt
import pandas
import sys

blocks = geopandas.read_file("seattle_census_blocks/seattle_blocks.shp")

blocks = blocks[["GEOID20", "geometry"]]

adjusted_pop = pandas.read_csv("WA_AdjustedPL_RCW4405140_Blocks_2020.csv")

blocks["GEOID20"] = pandas.to_numeric(blocks["GEOID20"], errors='coerce').convert_dtypes()

blocks = blocks.merge(adjusted_pop, on="GEOID20")

blocks = blocks[["GEOID20", "TAPERSONS", "geometry"]]

print(sum(blocks["TAPERSONS"]))

blocks = blocks[blocks["TAPERSONS"] > 0]

year = sys.argv[1]
print(year)

precincts = geopandas.read_file(f"votdst_area__historic_shp/votdst_area_{year}.shp")
precincts = precincts.to_crs(blocks.crs)
precincts = precincts.clip(blocks)
# Filter down to seattle precincts. (They all start with SEA.)
s = precincts["NAME"].str.split(" ", n=1, expand=True)
precincts = precincts[s[0] == "SEA"]
original_precints = precincts
print(precincts)
unbuffered = precincts["geometry"]

joined = precincts.sjoin(blocks, predicate="contains", how="right")
no_precinct = blocks[joined["index_left"].isna()]
joined = joined.dropna(subset=['index_left'])

# grow buffer boundaries until all blocks are contained within a precinct's bounds.
# If the growth causes two precincts to claim a block, then the first is kept.
buffer = 1
while not no_precinct.empty:
    print(buffer, len(no_precinct))
    precincts["geometry"] = unbuffered.buffer(buffer * 10)

    result = precincts.sjoin(no_precinct, predicate="contains", how="right")
    result = result.drop_duplicates(subset="GEOID20")
    unmatched = result["index_left"].isna()
    no_precinct = no_precinct[unmatched]
    joined = joined.append(result.dropna(subset=['index_left']))    
    buffer += 1

precinct_totals = joined[["NAME", "TAPERSONS"]].groupby(by="NAME").sum()
precinct_totals["total_TAPERSONS"] = precinct_totals["TAPERSONS"]
del precinct_totals["TAPERSONS"]
print(precinct_totals)

print("missing")
m = original_precints.join(precinct_totals, on="NAME")
empty = m[m["total_TAPERSONS"].isna()]
print(empty)

joined = joined.join(precinct_totals, on="NAME")

joined["fraction"] = joined["TAPERSONS"] / joined["total_TAPERSONS"]
print(sum(joined["TAPERSONS"]))
joined[["NAME", "GEOID20", "TAPERSONS", "total_TAPERSONS", "fraction"]].sort_values(by=["NAME", "GEOID20"]).to_csv(f"precincts/{year}.csv", index=False)

ax = joined.plot(column="votdst", figsize=(9*10,16*10))
unbuffered.boundary.plot(ax=ax, edgecolor="black")
empty.boundary.plot(ax=ax, edgecolor="red")
ax.set_axis_off()
ax.set_frame_on(False)
ax.margins(0)
ax.get_figure().savefig("precincts.png", bbox_inches='tight')

