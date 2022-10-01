import datetime
import inspect
import gerrymander
import driving_diameter_report
import topojson_districts
import population
import pandas
import parse
import pathlib
import split_report
import subprocess
import rentals
import road_report
import toml
import sys
import json
import zoning

import sqlite3

out = pathlib.Path("reports")

info = toml.load("maps/info.toml")

index_lines = ["# Map Proposals", ""]
full_lines = []

db = sqlite3.connect("report-cache.db")

cur = db.cursor()
try:
    cur.execute("CREATE TABLE report_content (map text, report text, last_update timestamp, content_json blob, UNIQUE(map, report))")
except sqlite3.OperationalError:
    pass

link = parse.compile("<img src=\"{img_url}\" alt=\"{alt}\" width=\"600px\">")

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
           ReportCache(zoning.ZoningReport()),
           ReportCache(rentals.RentalReport()),
           ReportCache(road_report.RoadReport()),
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
relevant_summaries = {}
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
    if i["relevant"]:
      full_lines.append(f"# {m.stem}")
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
        section_lines = ["## " + title] + sections.split("\n") + [""]
        lines.extend(section_lines)
        if title not in ("Districts", "Driving Diameter", "Gerrymander") and i["relevant"]:
          full_lines.extend(section_lines)
          if r not in relevant_summaries:
            relevant_summaries[r] = {}
          relevant_summaries[r][m.stem] = summary
    report.write_text("\n".join(lines))

index_lines.append("")

summary_lines = []
relevant_summary_lines = []
for r in reports:
    if r not in summaries:
      continue
    summary = r.summarize(summaries[r])
    relevant_summary = None
    if r in relevant_summaries:
      relevant_summary = r.summarize(relevant_summaries[r])
    if summary:
      summary_lines.append("## " + titles[r])
      summary_lines.append(summary)
      summary_lines.append("")
    if relevant_summary:
      relevant_summary_lines.append("## " + titles[r])
      relevant_summary_lines.append(relevant_summary)
      relevant_summary_lines.append("")

index_lines.append("# Summary Stats")
index_lines.extend(summary_lines)

full_lines = ["# Summary"] + relevant_summary_lines + full_lines

now = datetime.datetime.now()
git_version = subprocess.run("git describe --dirty --always", shell=True, capture_output=True, text=True)
git_version = git_version.stdout.strip()
full_lines += ["# Version", f"Generated {now} from code version {git_version}.",""]

for i, line in enumerate(full_lines):
  result = link.search(line)
  if result:
    alt = result.named["alt"]
    url = result.named["img_url"]
    full_lines[i] = f"![{alt}]({url})\\\n"

index = out / "README.md"
if len(sys.argv) > 1:
  pass
  # print("\n".join(index_lines))
else:
  index.write_text("\n".join(index_lines))

pdf_version = out / "full_pdf.md"
if len(sys.argv) > 1:
  pass
  # print("\n".join(full_lines))
else:
  full_text = "\n".join(full_lines)
  full_text = full_text.replace("🅰", "A")
  full_text = full_text.replace("🄱 ", "B")
  full_text = full_text.replace("✅", "PASS")
  full_text = full_text.replace("❌", "FAIL")
  pdf_version.write_text(full_text)
