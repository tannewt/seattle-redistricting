import gerrymander
import driving_diameter_report
import topojson_districts
import population
import pandas
import pathlib
import split_report
import road_report
import toml

out = pathlib.Path("reports")

info = toml.load("maps/info.toml")

index_lines = ["# Map Proposals", ""]

reports = [topojson_districts.TopoJSONReport(),
           population.PopulationReport(),
           driving_diameter_report.DrivingDiameterReport(),
           # road_report.RoadReport(),
           split_report.SplitReport("City Clerk Neighborhoods", "communities/city_clerk_neighborhoods.csv"),
           split_report.SplitReport("Atlas Neighborhoods", "communities/neighborhoods.csv"),
           split_report.SplitReport("Community Reporting Areas", "communities/reporting_areas.csv"),
           split_report.SplitReport("Elementary Schools 2021-22", "communities/elementary_schools.csv"),
           split_report.SplitReport("Middle Schools 2021-22", "communities/middle_schools.csv"),
           gerrymander.GerrymanderReport()
          ]

summaries = {}
titles = {}

for m in pathlib.Path("maps").iterdir():
    if m.name == "info.toml":
      continue
    report = out / (m.stem + ".md")
    if report.exists():
      continue
    print(m, m.stem)
    i = info[m.stem]
    context = i["context_url"]
    daves = i["daves_url"]
    index_lines.append(f"* {m.stem} [Report](./{m.stem}.md) | [Source]({context}) | [Dave's]({daves})")
    districts = pandas.read_csv(m)
    lines = []
    asset_dir = out / m.stem
    asset_dir.mkdir(exist_ok=True)
    for r in reports:
        title, sections, summary = r.content(districts, asset_directory=asset_dir)
        if r not in summaries:
            titles[r] = title
            summaries[r] = {}
        summaries[r][m.stem] = summary
        lines.append("## " + title)
        lines.append(sections)
        lines.append("")
    report.write_text("\n".join(lines))

index_lines.append("")

for r in reports:
    if hasattr(r, "summarize"):
      index_lines.append("# " + titles[r])
      index_lines.append(r.summarize(summaries[r]))
      index_lines.append("")

index = out / "README.md"
index.write_text("\n".join(index_lines))
