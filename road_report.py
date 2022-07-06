# This script was used to filter the blocks from the block20 redistricting data (too big for github)
# for washington to seattle. Seattle was defined by existing districts plus a polygon to bridge the
# ship canal.

import geopandas
import pandas
import sys
import osmnx
import networkx
import matplotlib.pyplot as plt

class RoadReport:

    def __init__(self):
        blocks = geopandas.read_file("seattle_census_blocks/seattle_blocks.shp")
        self.roads = osmnx.load_graphml("sources/roads.graphml")
        self.roads = osmnx.project_graph(self.roads, blocks.crs)
        self.roads = self.roads.subgraph(max(networkx.weakly_connected_components(self.roads), key=len))
        self.nodes = osmnx.graph_to_gdfs(self.roads, edges=False)
        blocks = blocks[["GEOID20", "geometry"]]
        blocks["GEOID20"] = pandas.to_numeric(blocks["GEOID20"], errors='coerce').convert_dtypes()
        self.blocks = blocks[["GEOID20", "geometry"]]

    def content(self, districts):
        lines = []
        blocks = self.blocks.merge(districts, on="GEOID20")
        del blocks["GEOID20"]

        joined = blocks.dissolve(by="District")
        for bounds in joined["geometry"]:
            intersecting_nodes = self.nodes[self.nodes.intersects(bounds.buffer(10))].index
            district_roads = self.roads.subgraph(intersecting_nodes)
            count = networkx.number_weakly_connected_components(district_roads)
            print(count)
            colors = osmnx.plot.get_colors(count)
            for i, sg in enumerate(networkx.weakly_connected_components(district_roads)):
                print(len(sg))
                for node in sg:
                    district_roads.nodes[node]["partition_size"] = i
            nc = osmnx.plot.get_node_colors_by_attr(district_roads, attr="partition_size")
            ax = joined[joined["geometry"]==bounds].boundary.plot(edgecolor="black")
            fig, new_ax = osmnx.plot_graph(district_roads, ax=ax, node_color=nc)

            print()
