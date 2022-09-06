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
        blocks = geopandas.read_file("seattle_census_blocks/seattle_blocks.shp")
        blocks = blocks[["GEOID20", "geometry"]]
        blocks["GEOID20"] = pandas.to_numeric(blocks["GEOID20"], errors='coerce').convert_dtypes()
        self.blocks = blocks[["GEOID20", "geometry"]]
        del self.areas["total_TAPERSONS"]

    def content(self, districts, asset_directory=None):
        lines = []
        blocks = districts.merge(self.areas, on="GEOID20")
        del blocks["GEOID20"]

        joined = blocks.groupby(["Name", "District"])

        by_area = joined.sum().sort_values(by="TAPERSONS", ascending=False).groupby(level=0)
        # print(by_area.tail(-1))

        img_url = asset_directory / f'split-{self.name}.png'
        block_shapes = self.blocks.merge(districts, on="GEOID20")
        district_shapes = block_shapes.dissolve(by="District")
        # print(block_shapes)
        block_shapes = block_shapes.merge(self.areas, on="GEOID20")
        area_shapes = block_shapes.dissolve(by="Name")
        area_count = block_shapes.merge(by_area.tail(-1), on=["Name", "District"])
        # print(area_count)
        # print(area_count.dtypes)
        ax = area_count.plot(column="TAPERSONS_x", cmap="Reds", figsize=(9*2,16*2))
        ax.set_axis_off()
        ax.set_frame_on(False)
        ax.margins(0)
        ax = area_shapes.boundary.plot(edgecolor="gray", ax=ax)
        area_shapes['coords'] = area_shapes['geometry'].apply(lambda x: x.representative_point().coords[:])
        area_shapes['coords'] = [coords[0] for coords in area_shapes['coords']]
        for idx, row in area_shapes.iterrows():
            plt.annotate(idx, xy=row['coords'],
                         horizontalalignment='center', fontsize="large",
                         fontweight="bold")
        ax = district_shapes.boundary.plot(edgecolor="black", ax=ax)
        ax.get_figure().savefig(img_url, bbox_inches='tight')
        img_url = str(img_url)[len("reports/"):]

        by_area = joined.sum().sort_values(by="TAPERSONS", ascending=False)
        by_area = by_area[by_area["TAPERSONS"] > 0]
        by_area = by_area.groupby(level=0)
        split_off = by_area.tail(-1).groupby(by="Name").sum().sort_values("TAPERSONS", ascending=False)
        split_people = split_off.sum().sum()
        total_people = by_area.sum()
        split_count = (by_area.count() > 1).value_counts()
        lines.append(f"This districting splits {split_count[True]} out of {split_count.sum()} areas. A person was split from an area {split_people} times.")
        lines.append("")
        lines.append(f"<img src=\"{img_url}\" alt=\"Map showing areas of population that have been split off.\" width=\"600px\">")
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
        lines.append("")

        lines.append("<details>")
        lines.append(f"<summary>{split_count[False]} kept whole</summary>")
        lines.append("")
        whole = joined.sum()[by_area.count() == 1].dropna().sort_values(by=["District", "Name"])

        table = [["Area", "District", "Population", "Percent"]]
        for area, district in whole.index:
            value = whole.loc[(area, district)]
            percent = value[0] * 100 / total_people.loc[area]
            table.append([area, str(district), f"{int(value[0]):d}", f"{percent[0]:0.2f}%"])
        table = table_from_string_list(table)
        lines.append(generate_markdown(table))
        lines.append("")
        lines.append("</details>")

        # print(lines)
        return (self.name, "\n".join(lines), split_people)

    def summarize(self, summaries):
        lines = []
        order = sorted(summaries.items(), key=lambda x: x[1])
        for i, (stem, count) in enumerate(order):
            lines.append(f"{i+1}. [{stem}](./{stem}.md) {count}")
        return "\n".join(lines)
