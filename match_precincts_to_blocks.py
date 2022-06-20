# This script was used to filter the blocks from the block20 redistricting data (too big for github)
# for washington to seattle. Seattle was defined by existing districts plus a polygon to bridge the
# ship canal.

import geopandas
import pathlib
import matplotlib.pyplot as plt
import pandas
import sys

blocks = geopandas.read_file("seattle_census_blocks/seattle_blocks.shp")

blocks = blocks[["GEOID20", "geometry", "P00010001"]]

print(sum(blocks["P00010001"]))

precincts = geopandas.read_file("votdst_area__historic_shp/votdst_area_2020.shp")
precincts = precincts.to_crs(blocks.crs)
print(precincts)

joined = precincts.sjoin(blocks, predicate="contains", how="right")
joined = joined.dropna(subset=['index_left'])

print(sum(joined["P00010001"]))

print(joined)

precincts.plot(figsize=(9,16), edgecolor="black")
ax = joined.plot(figsize=(9,16))
ax.set_axis_off()
ax.set_frame_on(False)
ax.margins(0)
ax.get_figure().savefig("precincts.png", bbox_inches='tight')
