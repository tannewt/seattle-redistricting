# This script was used to filter the blocks from the block20 redistricting data (too big for github)
# for washington to seattle. Seattle was defined by existing districts plus a polygon to bridge the
# ship canal.
#
# Original block20 data is from: https://ofm.wa.gov/washington-data-research/population-demographics/gis-data/census-geographic-files

import geopandas
import pathlib

existing_districts = geopandas.read_file("Seattle_City_Council_Districts___sccdst_area/modified.shp")

census_data = geopandas.read_file("block20/wa_2020_pl94171_block.dbf")
print(type(census_data))
print(census_data)

blocks = geopandas.read_file("block20/block20.shp")
print(type(blocks))
print(blocks)

del census_data["geometry"]
merged = blocks.merge(census_data, on="GEOID20")
print(type(merged))
print(merged)

existing_districts = existing_districts.to_crs(blocks.crs)

filtered = merged.clip(existing_districts)
print(type(filtered))
print(filtered)

filtered.plot().get_figure().savefig("seattle.png")

filtered.to_file("seattle_blocks.shp")
