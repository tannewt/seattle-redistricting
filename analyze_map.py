# This script was used to filter the blocks from the block20 redistricting data (too big for github)
# for washington to seattle. Seattle was defined by existing districts plus a polygon to bridge the
# ship canal.

import geopandas
import pathlib
import matplotlib.pyplot as plt

blocks = geopandas.read_file("seattle_census_blocks/seattle_blocks.shp")

total18 = "P00030001"
white_alone18 = "P00030003"

blocks = blocks[blocks[total18] > 0]

blocks["nonwhite"] = (blocks[total18] - blocks[white_alone18]) - blocks[white_alone18]

print(blocks)

row = blocks[blocks["GEOID20"] == "530330047011001"]

print(row)

for col in row.columns.to_list():
    print(col, row[col][7458])

plt.figure()

ax = blocks.plot(column='POPDEN', cmap='OrRd',figsize=(9,16))
ax.set_axis_off()
ax.set_frame_on(False)
ax.margins(0)
ax.get_figure().savefig("seattle2.png", bbox_inches='tight')

ax = blocks.plot(column='nonwhite',figsize=(9,16))
ax.set_axis_off()
ax.set_frame_on(False)
ax.margins(0)
ax.get_figure().savefig("seattle_white.png", bbox_inches='tight')
