# This script was used to filter the blocks from the block20 redistricting data (too big for github)
# for washington to seattle. Seattle was defined by existing districts plus a polygon to bridge the
# ship canal.

import geopandas
import pandas
import sys
import osmnx
import networkx

class RoadReport:

    def __init__(self):
        self.roads = osmnx.load_graphml("sources/roads.graphml")
        self.roads = self.roads.subgraph(max(networkx.strongly_connected_components(self.roads), key=len))
        self.nodes = osmnx.graph_to_gdfs(self.roads, edges=False)
        blocks = geopandas.read_file("seattle_census_blocks/seattle_blocks.shp")
        self.nodes = self.nodes.to_crs(blocks.crs)
        blocks = blocks[["GEOID20", "geometry"]]
        blocks["GEOID20"] = pandas.to_numeric(blocks["GEOID20"], errors='coerce').convert_dtypes()
        self.blocks = blocks[["GEOID20", "geometry"]]

    def content(self, districts):
        lines = []
        blocks = self.blocks.merge(districts, on="GEOID20")
        del blocks["GEOID20"]

        joined = blocks.dissolve(by="District")
        for bounds in joined["geometry"]:
            intersecting_nodes = self.nodes[self.nodes.intersects(bounds.buffer(50))].index
            district_roads = self.roads.subgraph(intersecting_nodes)
            for sg in networkx.strongly_connected_components(district_roads):
                print(len(sg))
            print()
