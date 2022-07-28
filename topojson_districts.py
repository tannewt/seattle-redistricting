
import pandas
import pathlib
import geopandas

class TopoJSONReport:
    def content(self, plan, asset_directory=None):
        blocks = geopandas.read_file("seattle_census_blocks/seattle_blocks.shp")
        blocks = blocks[["GEOID20", "geometry"]]
        blocks["GEOID20"] = pandas.to_numeric(blocks["GEOID20"], errors='coerce').convert_dtypes()
        district_bounds = blocks.merge(plan, on="GEOID20")
        district_bounds = district_bounds.dissolve(by="District")
        district_bounds = district_bounds.to_crs("urn:ogc:def:crs:OGC:1.3:CRS84")
        json = district_bounds.to_json(show_bbox=True)
        return ("Districts", "```geojson\n" + json + "\n```", None)
