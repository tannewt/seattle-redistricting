# This script was used to filter the blocks from the block20 redistricting data (too big for github)
# for washington to seattle. Seattle was defined by existing districts plus a polygon to bridge the
# ship canal.

import geopandas
import pathlib
import matplotlib.pyplot as plt
import pandas
import sys
from markdown_table_generator import generate_markdown, table_from_string_list

class SplitReport:

    def __init__(self, name, areas):
        self.name = name
        self.areas = pandas.read_csv(areas)
        del self.areas["total_TAPERSONS"]

    def content(self, districts, asset_directory=None):
        lines = []
        blocks = districts.merge(self.areas, on="GEOID20")
        del blocks["GEOID20"]

        joined = blocks.groupby(["Name", "District"])


        by_area = joined.sum().sort_values(by="TAPERSONS", ascending=False).groupby(level=0)
        total_people = by_area.sum()
        split_count = (by_area.count() > 1).value_counts()
        split_off = by_area.tail(-1).groupby(by="Name").sum().sort_values("TAPERSONS", ascending=False)
        lines.append(f"This districting splits {split_count[True]} out of {split_count.sum()} areas. A person was split from an area {split_off.sum().sum()} times.")
        lines.append("")
        table = [["Area", "District", "Population", "Percent"]]
        for area in split_off.index:
            for i, row in enumerate(by_area.get_group(area).iterrows()):
                index, value = row
                name, district = index
                percent = value[0] * 100 / total_people.loc[name]
                if i > 0:
                    name = ""
                table.append([name, str(district), f"{value[0]:d}", f"{percent[0]:0.2f}%"])
        table = table_from_string_list(table)
        lines.append(generate_markdown(table))
        # print(lines)
        return (self.name, "\n".join(lines))
