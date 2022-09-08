import inspect
import gerrymander
import driving_diameter_report
import topojson_districts
import population
import pandas
import pathlib
import split_report
import road_report
import toml
import sys
import json

import sqlite3

out = pathlib.Path("reports")

info = toml.load("maps/info.toml")

index_lines = ["# Map Proposals", ""]

db = sqlite3.connect("report-cache.db")

cur = db.cursor()
try:
    cur.execute("CREATE TABLE report_content (map text, report text, last_update timestamp, content_json blob, UNIQUE(map, report))")
except sqlite3.OperationalError:
    pass

class ReportCache:
  def __init__(self, delegate):
    source_code_file = pathlib.Path(inspect.getfile(delegate.__class__))
    self.delegate = delegate

    self.source_change = source_code_file.stat().st_mtime

  def content(self, district_path, districts, asset_directory=None):
    cur = db.cursor()
    cur.execute("SELECT last_update, content_json FROM report_content WHERE map = ? AND report = ?", (str(district_path), repr(self.delegate)))
    past_run = cur.fetchone()
    newest_change = max(self.source_change, district_path.stat().st_mtime)
    if past_run is None or past_run[0] < newest_change:
        result = self.delegate.content(districts, asset_directory)
        new_row = (str(district_path), repr(self.delegate), newest_change, json.dumps(result))
        db.execute("INSERT INTO report_content (map, report, last_update, content_json) VALUES (?, ?, ?, ?) ON CONFLICT (map, report) DO UPDATE SET last_update = excluded.last_update, content_json = excluded.content_json", new_row)
        db.commit()
        return result
    else:
      print(str(district_path), repr(self.delegate), "cached")
    return json.loads(past_run[1])

  def summarize(self, summaries):
    if not hasattr(self.delegate, "summarize"):
      return ""
    # Don't cache this because the summaries may be partially cached.
    return self.delegate.summarize(summaries)

reports = [ReportCache(topojson_districts.TopoJSONReport()),
           ReportCache(population.PopulationReport()),
           ReportCache(driving_diameter_report.DrivingDiameterReport()),
           # road_report.RoadReport(),
           ReportCache(split_report.SplitReport("City Clerk Neighborhoods", "communities/city_clerk_neighborhoods.csv")),
           ReportCache(split_report.SplitReport("Atlas Neighborhoods", "communities/neighborhoods.csv")),
           ReportCache(split_report.SplitReport("Community Reporting Areas", "communities/reporting_areas.csv")),
           ReportCache(split_report.SplitReport("Elementary Schools 2021-22", "communities/elementary_schools.csv")),
           ReportCache(split_report.SplitReport("Middle Schools 2021-22", "communities/middle_schools.csv")),
           ReportCache(split_report.SplitReport("Police Beats 2018 - Present", "communities/police_beats.csv")),
           ReportCache(split_report.SplitReport("2022 Voting Precincts", "precincts/2022.csv")),
           ReportCache(gerrymander.GerrymanderReport())
          ]

summaries = {}
titles = {}

for m in pathlib.Path("maps").iterdir():
    if m.name == "info.toml":
      continue
    report = out / (m.stem + ".md")
    if len(sys.argv) > 1 and str(m) not in sys.argv[1:]:
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
        title, sections, summary = r.content(m, districts, asset_directory=asset_dir)
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
    summary = r.summarize(summaries[r])
    if summary:
      index_lines.append("# " + titles[r])
      index_lines.append(summary)
      index_lines.append("")

index = out / "README.md"
if len(sys.argv) > 1:
  print("\n".join(index_lines))
else:
  index.write_text("\n".join(index_lines))
