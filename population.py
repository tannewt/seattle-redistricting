# This script was used to filter the blocks from the block20 redistricting data (too big for github)
# for washington to seattle. Seattle was defined by existing districts plus a polygon to bridge the
# ship canal.

import geopandas
import pathlib
import matplotlib.pyplot as plt
import pandas
import sys
from markdown_table_generator import generate_markdown, table_from_string_list

class PopulationReport:

    def __init__(self):
        self.adjusted_pop = pandas.read_csv("WA_AdjustedPL_RCW4405140_Blocks_2020.csv")

    def __repr__(self):
        return "PopulationReport()"

    def content(self, districts, asset_directory=None):
        lines = []
        blocks = districts.merge(self.adjusted_pop, on="GEOID20")

        totals = blocks.groupby(["District"]).sum()

        max_pop = max(totals["TAPERSONS"])
        min_pop = min(totals["TAPERSONS"])
        spread = max_pop / min_pop
        status = "✅"
        if spread > 1.01:
            status = "❌"

        lines.append(f"{status} - The maximum population ({max_pop}) is {spread * 100 - 100:0.2f}% greater than the minimum ({min_pop}).")
        lines.append("")
        title = f"Population"
        totals = totals[totals.columns[1:]]
        lines.append("### Census Groups")
        rows = [["Stat", "1", "2", "3", "4", "5", "6", "7"]]
        for c in totals.columns:
            if c not in ("TAPERSONS", "TAHOUSING", "TAHOCCUPID", "TAHVACANT", "TAGRPQRTR"):
                percent = totals[c] * 100 / totals["TAPERSONS"]
                rows.append([c] + [f"{x:0.1f}%" for x in percent.tolist()])
            else:
                rows.append([c] + [str(x) for x in totals[c].tolist()])
        table = table_from_string_list(rows)
        markdown = generate_markdown(table)
        lines.append(markdown)
        return (title, "\n".join(lines), f"{status} +{spread * 100 - 100:0.2f}%")

    def summarize(self, summaries):
        lines = []
        for stem, status in summaries.items():
            lines.append(f"* [{stem}](./{stem}.md) {status}")
        return "\n".join(lines)
