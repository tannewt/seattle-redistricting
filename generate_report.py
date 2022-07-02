import gerrymander
import population
import pandas
import pathlib

out = pathlib.Path("reports")

for m in pathlib.Path("maps").iterdir():
    print(m)
    districts = pandas.read_csv(m)
    lines = []
    for r in [population.PopulationReport(), gerrymander.GerrymanderReport()]:
        title, sections = r.content(districts)
        lines.append("## " + title)
        lines.append(sections)
        lines.append("")
    report = out / (m.stem + ".md")
    report.write_text("\n".join(lines))
