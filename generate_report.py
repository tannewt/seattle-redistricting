import gerrymander
import driving_diameter_report
import topojson_districts
import population
import pandas
import pathlib
import split_report
import road_report

out = pathlib.Path("reports")

for m in pathlib.Path("maps").iterdir():
    print(m, m.stem)
    districts = pandas.read_csv(m)
    lines = []
    asset_dir = out / m.stem
    asset_dir.mkdir(exist_ok=True)
    for r in [topojson_districts.TopoJSONReport(),
              population.PopulationReport(),
              driving_diameter_report.DrivingDiameterReport(),
              # road_report.RoadReport(),
              split_report.SplitReport("City Clerk Neighborhoods", "communities/city_clerk_neighborhoods.csv"),
              split_report.SplitReport("Atlas Neighborhoods", "communities/neighborhoods.csv"),
              split_report.SplitReport("Community Reporting Areas", "communities/reporting_areas.csv"),
              split_report.SplitReport("Elementary Schools 2021-22", "communities/elementary_schools.csv"),
              split_report.SplitReport("Middle Schools 2021-22", "communities/middle_schools.csv"),
              gerrymander.GerrymanderReport()
              ]:
        title, sections = r.content(districts, asset_directory=asset_dir)
        lines.append("## " + title)
        lines.append(sections)
        lines.append("")
    report = out / (m.stem + ".md")
    report.write_text("\n".join(lines))
