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
    print(m)
    districts = pandas.read_csv(m)
    lines = []
    for r in [driving_diameter_report.DrivingDiameterReport(),
              # road_report.RoadReport(),
              # population.PopulationReport(),
              # split_report.SplitReport("Atlas Neighborhoods", "communities/neighborhoods.csv"),
              # split_report.SplitReport("Community Reporting Areas", "communities/reporting_areas.csv"),
              # split_report.SplitReport("Elementary Schools 2021-22", "communities/elementary_schools.csv"),
              # split_report.SplitReport("Middle Schools 2021-22", "communities/middle_schools.csv"),
              # gerrymander.GerrymanderReport(),
              # topojson_districts.TopoJSONReport()
              ]:
        title, sections = r.content(districts)
        lines.append("## " + title)
        lines.append(sections)
        lines.append("")
    report = out / (m.stem + ".md")
    report.write_text("\n".join(lines))
