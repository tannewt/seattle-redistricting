import geopandas
import pathlib
import matplotlib.pyplot as plt
import matplotlib
import pandas
import sys

LOW_COMMERCIAL = "#AAAAFF"
MED_COMMERCIAL = "#5555FF"
HIGH_COMMERCIAL = "#0000D4"

LOW_RESIDENTIAL = "#8DD35F"
MED_RESIDENTIAL = "#5AA02C"
HIGH_RESIDENTIAL = "#447821"

LOW_INDUSTRIAL = "#FFDD55"
MED_INDUSTRIAL = "#FFCC00"
HIGH_INDUSTRIAL = "#D4AA00"

SPECIAL = "#999999"

MAPPING = {
    "NR1": LOW_RESIDENTIAL,
    "NR2": LOW_RESIDENTIAL,
    "NR3": LOW_RESIDENTIAL,
    "RSL": LOW_RESIDENTIAL,
    "LR1": MED_RESIDENTIAL,
    "LR2": MED_RESIDENTIAL,
    "LR3": MED_RESIDENTIAL,
    "MR": MED_RESIDENTIAL,
    "HR": HIGH_RESIDENTIAL,
    "NC1": LOW_COMMERCIAL,
    "NC1P": LOW_COMMERCIAL,
    "C1": LOW_COMMERCIAL,
    "C1P": LOW_COMMERCIAL,
    "C2": MED_COMMERCIAL,
    "C2P": MED_COMMERCIAL,
    "SM": HIGH_COMMERCIAL,
    "PSM": MED_COMMERCIAL,
    "DMC": HIGH_COMMERCIAL,
    "DMR/C": HIGH_COMMERCIAL,
    "DMR/R": HIGH_RESIDENTIAL,
    "DOC1": HIGH_COMMERCIAL,
    "DOC2": HIGH_COMMERCIAL,
    "DRC": HIGH_COMMERCIAL,
    "DH1/45": MED_COMMERCIAL,
    "DH2/55": MED_COMMERCIAL,
    "DH2/75": MED_COMMERCIAL,
    "DH2/85": MED_COMMERCIAL,
    "NC2": MED_COMMERCIAL,
    "NC2P": MED_COMMERCIAL,
    "NC3": MED_COMMERCIAL,
    "NC3P": MED_COMMERCIAL,
    "IG1": MED_INDUSTRIAL,
    "IG2": MED_INDUSTRIAL,
    "IB": LOW_INDUSTRIAL,
    "IC": LOW_INDUSTRIAL,
    "IDM": MED_COMMERCIAL,
    "IDR": HIGH_RESIDENTIAL,
    "IDR/C": HIGH_COMMERCIAL,
    "PMM": MED_COMMERCIAL,
    "MPC": HIGH_COMMERCIAL,

}

class ZoningReport:

    def __init__(self):
        self.zones = geopandas.read_file("sources/Zoning_with_Development_Assumptions.geojson")
        blocks = geopandas.read_file("seattle_census_blocks/seattle_blocks.shp")
        blocks = blocks[["GEOID20", "geometry"]]
        blocks["GEOID20"] = pandas.to_numeric(blocks["GEOID20"], errors='coerce').convert_dtypes()
        self.blocks = blocks[["GEOID20", "geometry"]]
        self.zones = self.zones.to_crs(self.blocks.crs)
        color_list = []
        zones = {}
        for i, row in self.zones.iterrows():
            zone = row["ZONING"]
            start = zone.replace("-", " ").split(" ")[0]
            if start == "MIO":
                start = zone.replace("-", " ").split(" ")[2]
            if zone in MAPPING:
                color_list.append(MAPPING[zone])
            elif start in MAPPING:
                # print(start, zone)
                color_list.append(MAPPING[start])
            else:
                if zone not in zones:
                    zones[zone] = 0
                zones[zone] += 1
                color_list.append("#ff00ff")
        # print()
        # for zone in zones:
        #     print(zone, zones[zone])
        self.cmap = matplotlib.colors.ListedColormap(color_list)

    def __repr__(self):
        return f"ZoningReport()"

    def content(self, districts, asset_directory=None):
        lines = ["This map simplifies city zoning into three categories:",
                 "",
                 "* Residential (Green)",
                 "* Commercial (Blue) and Residential is also allowed",
                 "* Industrial (Yellow)",
                 "",
                 "Denser areas are darker than lighter ones. There are three gradations of density.",
                 ""]

        img_url = asset_directory / f'zoning.png'
        block_shapes = self.blocks.merge(districts, on="GEOID20")
        district_shapes = block_shapes.dissolve(by="District")
        ax = self.zones.plot(cmap=self.cmap, figsize=(9*2,16*2))
        ax.set_axis_off()
        ax.set_frame_on(False)
        ax.margins(0)
        ax = district_shapes.boundary.plot(edgecolor="black", ax=ax)
        ax.get_figure().savefig(img_url, bbox_inches='tight')
        # print("saved", img_url)
        img_url = str(img_url)[len("reports/"):]
        lines.append(f"<img src=\"{img_url}\" alt=\"Map showing district lines over zoning map.\" width=\"600px\">")
        lines.append("")

        # print(lines)
        return ("Zoning", "\n".join(lines), None)
