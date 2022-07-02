import gerrymander
import topojson_districts
import population
import pandas
import pathlib

out = pathlib.Path("reports")

for m in pathlib.Path("maps").iterdir():
    print(m)
    districts = pandas.read_csv(m)
    lines = []
    for r in [population.PopulationReport(),
              gerrymander.GerrymanderReport(),
              topojson_districts.TopoJSONReport()]:
        title, sections = r.content(districts)
        lines.append("## " + title)
        lines.append(sections)
        lines.append("")
    report = out / (m.stem + ".md")
    report.write_text("\n".join(lines))
