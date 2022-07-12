import warnings
warnings.filterwarnings(action="ignore")

import pandas
import pathlib
import geopandas
from markdown_table_generator import generate_markdown, table_from_string_list

from matplotlib import colors


class GerrymanderReport:
    def output_election(self, options):
        total_votes = None
        option_totals = {}
        district_winners = [("A", 0)] * 7
        for k in options:
            o = options[k]
            option_totals[k] = sum(o)
            for i in range(1,8):
                votes = options[k][i]
                if votes > district_winners[i - 1][1]:
                    district_winners[i - 1] = (k, votes)
            if total_votes is None:
                total_votes = o.copy()
            else:
                total_votes += o
        district_result = dict(((k, 0) for k in options))
        # print(a, b)
        a, b = option_totals.keys()
        options["diff"] = options[a] - options[b]
        # print(options["diff"] * 100 / total_votes)
        for d in district_winners:
            district_result[d[0]] += 100 / 7
        a_percent = option_totals[a] * 100 / sum(total_votes)
        b_percent = option_totals[b] * 100 / sum(total_votes)

        return [f"{a_percent:.1f}%",
                f"{b_percent:.1f}%",
                f"{district_result[a]:.1f}%",
                f"{district_result[b]:.1f}%"] + ["🅰" if x[0] == a else "🄱" for x in district_winners]

    def content(self, plan, asset_directory=None):
        elections = pathlib.Path("elections")
        blocks = geopandas.read_file("seattle_census_blocks/seattle_blocks.shp")
        blocks = blocks[["GEOID20", "geometry"]]
        blocks["GEOID20"] = pandas.to_numeric(blocks["GEOID20"], errors='coerce').convert_dtypes()
        district_bounds = blocks.merge(plan, on="GEOID20")
        district_bounds = district_bounds.dissolve(by="District")
        rows = [["Race", "🅰", "🄱", "D🅰", "D🄱", "1", "2", "3", "4", "5", "6", "7"]]
        for election in elections.iterdir():
            year = election.name[:4]
            precincts = pandas.read_csv(f"precincts/{year}.csv")
            election = pandas.read_csv(election, header=[0, 1], index_col=0)
            results = precincts.merge(election, left_on="NAME", right_index=True)
            for c in results:
                if c != "Precinct":
                    continue
                results[c] = results[c] * results["TAPERSONS"] // results["total_TAPERSONS"]

            results = results.merge(plan, on="GEOID20")

            districts = results.groupby(by="District").sum()
            s = districts.sum()
            current_election = None
            options = {}
            i = 1
            for c in districts.columns:
                if not isinstance(c, tuple):
                    continue
                election, option = c
                if current_election != election:
                    if current_election:
                        fn = election.replace(" ", "_") + ".png"
                        a, b = options.keys()
                        race = results[["GEOID20", "District"]]
                        race["diff"] = results[(current_election, a)] - results[(current_election, b)]
                        race = blocks.merge(race, on="GEOID20")

                        # ax = race.plot(column="diff", figsize=(9*10,16*10), norm=colors.CenteredNorm(), cmap="coolwarm")
                        # ax.set_axis_off()
                        # ax.set_frame_on(False)
                        # ax.margins(0)
                        # district_bounds.boundary.plot(ax=ax, edgecolor="black")
                        # print(fn)
                        # ax.get_figure().savefig(fn, bbox_inches='tight')
                        rows.append([f"{year}.11.{i}"] + self.output_election(options))
                        options = {}
                        i += 1
                    current_election = election
                options[option] = districts[c]

            rows.append([f"{year}.11.{i}"] + self.output_election(options))

        table = table_from_string_list(rows)
        markdown = generate_markdown(table)
        return ("Gerrymander", markdown)
