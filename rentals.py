import geopandas
import pathlib
import matplotlib.pyplot as plt
import matplotlib
import numpy
import pandas
import sys

from markdown_table_generator import generate_markdown, table_from_string_list

class RentalReport:

    def __init__(self):
        rental_info = geopandas.read_file("sources/Rental_Property_Registration.csv")
        rental_info["Location1"].replace('', numpy.nan, inplace=True)
        rental_info = rental_info.dropna(subset=["Location1"])
        rental_info["geometry"] = geopandas.points_from_xy(rental_info["Longitude"], rental_info["Latitude"], crs="EPSG:4326")
        
        blocks = geopandas.read_file("seattle_census_blocks/seattle_blocks.shp")
        blocks = blocks[["GEOID20", "geometry"]]
        blocks["GEOID20"] = pandas.to_numeric(blocks["GEOID20"], errors='coerce').convert_dtypes()
        self.all_blocks = blocks
        rental_info = rental_info.to_crs(blocks.crs)
        rental_info["RentalHousingUnits"] = pandas.to_numeric(rental_info["RentalHousingUnits"])

        # unit_count = rental_info[["RentalHousingUnits", "geometry"]]
        unit_count = rental_info

        joined = unit_count.sjoin(blocks, how="inner", predicate="intersects")
        joined = joined[["RentalHousingUnits", "GEOID20"]]
        summed = joined.groupby(by="GEOID20").sum()
        self.blocks = blocks.merge(summed, on="GEOID20")

    def __repr__(self):
        return f"RentalReport()"

    def content(self, districts, asset_directory=None):
        lines = ["Count of rental housing units (not renters themselves) per district. Sourced from [Rental Property Registration](https://data.seattle.gov/Permitting/Rental-Property-Registration/j2xh-c7vt) on September 29th, 2022.", ""]

        img_url = asset_directory / f'rentals.png'
        block_shapes = self.all_blocks.merge(districts, on="GEOID20")
        district_shapes = block_shapes.dissolve(by="District")

        rentals_per_district = self.blocks.merge(districts, on="GEOID20").groupby(by="District").sum()

        table = [["District", "Rental Housing Units"]]
        for district, values in rentals_per_district.iterrows():
            rhu = values["RentalHousingUnits"]
            table.append([str(district), f"{rhu:d}"])
        table = table_from_string_list(table)

        ax = self.blocks.plot(column="RentalHousingUnits", cmap="Reds", figsize=(9*2,16*2), legend=True)
        ax.set_axis_off()
        ax.set_frame_on(False)
        ax.margins(0)

        ax = district_shapes.boundary.plot(edgecolor="black", ax=ax)
        ax.get_figure().savefig(img_url, bbox_inches='tight')
        img_url = str(img_url)[len("reports/"):]
        lines.append(f"<img src=\"{img_url}\" alt=\"Map showing district lines over map of rental unit quantity.\" width=\"600px\">")
        lines.append("")
        lines.append(generate_markdown(table))

        return ("Rental Units", "\n".join(lines), None)
