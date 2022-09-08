# This script was used to filter the blocks from the block20 redistricting data (too big for github)
# for washington to seattle. Seattle was defined by existing districts plus a polygon to bridge the
# ship canal.

import warnings
warnings.filterwarnings(action="ignore")

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

def _map_areas(precincts, name_key, output_file):
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

    precinct_totals = joined[[name_key, "TAPERSONS"]].groupby(by=name_key).sum()
    precinct_totals["total_TAPERSONS"] = precinct_totals["TAPERSONS"]
    del precinct_totals["TAPERSONS"]
    print(precinct_totals)

    print("missing")
    m = original_precints.join(precinct_totals, on=name_key)
    empty = m[m["total_TAPERSONS"].isna()]
    print(empty)

    joined = joined.join(precinct_totals, on=name_key)

    print(sum(joined["TAPERSONS"]))
    joined[[name_key, "GEOID20", "TAPERSONS", "total_TAPERSONS"]].sort_values(by=[name_key, "GEOID20"]).to_csv(output_file, index=False)

    ax = joined.plot(column=name_key, figsize=(9*2,16*2))
    unbuffered.boundary.plot(ax=ax, edgecolor="black")
    empty.boundary.plot(ax=ax, edgecolor="red")
    ax.set_axis_off()
    ax.set_frame_on(False)
    ax.margins(0)
    ax.get_figure().savefig(output_file + ".png", bbox_inches='tight')

schools = geopandas.read_file("sources/Seattle_Public_Schools_Elementary_School_Attendance_Areas_2021-22/Seattle_Public_Schools_Elementary_School_Attendance_Areas_2021-22.shp")
schools = schools.to_crs(blocks.crs)
middle_schools = schools.dissolve(by="MS_ZONE", as_index=False)
middle_schools["Name"] = middle_schools["MS_ZONE"]
_map_areas(middle_schools,
           "Name", "communities/middle_schools.csv")
schools["Name"] = schools["ES_ZONE"]
_map_areas(schools,
           "Name", "communities/elementary_schools.csv")

cra = geopandas.read_file("sources/Community_Reporting_Areas/CITYPLAN_CRA.shp")
cra = cra.to_crs(blocks.crs)
cra["Name"] = cra["GEN_ALIAS"]
_map_areas(cra,
           "Name", "communities/reporting_areas.csv")

cc_neighborhoods = geopandas.read_file("sources/City_Clerk_Neighborhoods/City_Clerk_Neighborhoods.shp")
print(cc_neighborhoods.dtypes)
print(cc_neighborhoods)
cc_neighborhoods = cc_neighborhoods.to_crs(blocks.crs)
cc_neighborhoods["Name"] = cc_neighborhoods["S_HOOD"]
_map_areas(cc_neighborhoods,
           "Name", "communities/city_clerk_neighborhoods.csv")

neighborhoods = geopandas.read_file("sources/Neighborhood_Map_Atlas_Districts/Neighborhood_Map_Atlas_Districts.shp")
neighborhoods = neighborhoods.to_crs(blocks.crs)
neighborhoods["Name"] = neighborhoods["L_HOOD"]
_map_areas(neighborhoods,
           "Name", "communities/neighborhoods.csv")

beats = geopandas.read_file("sources/Seattle_Police_Beats_2018-Present/Seattle_Police_Beats_2018-Present.shp")
beats = beats.to_crs(blocks.crs)
print(beats)
beats["Name"] = beats["beat"]
_map_areas(beats,
           "Name", "communities/police_beats.csv")


    precincts = precincts[s[0] == "SEA"]
    _map_areas(precincts, "NAME", f"precincts/{year}.csv")

year = 2022
print(year)
precincts = geopandas.read_file(f"Voting_Districts_of_King_County___votdst_area/Voting_Districts_of_King_County___votdst_area.shp")
precincts = precincts.to_crs(blocks.crs)
precincts = precincts.clip(blocks)
# Filter down to seattle precincts. (They all start with SEA.)
s = precincts["NAME"].str.split(" ", n=1, expand=True)
precincts = precincts[s[0] == "SEA"]
precincts["Name"] = precincts["NAME"]
_map_areas(precincts, "Name", f"precincts/{year}.csv")
