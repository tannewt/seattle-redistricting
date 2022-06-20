# This script was used to filter the blocks from the block20 redistricting data (too big for github)
# for washington to seattle. Seattle was defined by existing districts plus a polygon to bridge the
# ship canal.

import geopandas
import pathlib
import matplotlib.pyplot as plt
import pandas
import sys

blocks = geopandas.read_file("seattle_census_blocks/seattle_blocks.shp")

adjusted_pop = pandas.read_csv("WA_AdjustedPL_RCW4405140_Blocks_2020.csv")
print(adjusted_pop)

assignments = pandas.read_csv(sys.argv[1])

blocks["GEOID20"] = pandas.to_numeric(blocks["GEOID20"], errors='coerce').convert_dtypes()

blocks = blocks.merge(assignments, on="GEOID20").merge(adjusted_pop, on="GEOID20")

print(blocks)

print(blocks.groupby(["District"]).sum()[["P00010001", "TAPERSONS"]])
