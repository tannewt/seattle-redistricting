
import pandas
import pathlib
import geopandas

class TopoJSONReport:
    def content(self, plan):
        blocks = geopandas.read_file("seattle_census_blocks/seattle_blocks.shp")
        blocks = blocks[["GEOID20", "geometry"]]
        blocks["GEOID20"] = pandas.to_numeric(blocks["GEOID20"], errors='coerce').convert_dtypes()
        district_bounds = blocks.merge(plan, on="GEOID20")
        district_bounds = district_bounds.dissolve(by="District")
        json = district_bounds.to_json()
        return ("Districts", "```geojson\n" + json + "\n```")
