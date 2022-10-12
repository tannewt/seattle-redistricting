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

    def __repr__(self):
        return "RoadReport()"

    def content(self, districts, asset_directory=None):
        lines = []
        blocks = self.blocks.merge(districts, on="GEOID20")
        del blocks["GEOID20"]

        joined = blocks.dissolve(by="District")
        d = 1
        disconnected = []
        maps = []
        for bounds in joined["geometry"]:
            intersecting_nodes = self.nodes[self.nodes.intersects(bounds.buffer(10))].index
            district_roads = self.roads.subgraph(intersecting_nodes)
            count = networkx.number_weakly_connected_components(district_roads)
            colors = osmnx.plot.get_colors(count)
            partition_count = 0
            for i, sg in enumerate(networkx.weakly_connected_components(district_roads)):
                if len(sg) > 10:
                    partition_count += 1
                for node in sg:
                    district_roads.nodes[node]["partition_size"] = i
            if partition_count > 1:
                disconnected.append(d)
            else:
                d += 1
                continue
            nc = osmnx.plot.get_node_colors_by_attr(district_roads, attr="partition_size")
            ax = joined[joined["geometry"]==bounds].boundary.plot(edgecolor="black")
            img_url = asset_directory / f'district{d}_roads.png'
            fig, new_ax = osmnx.plot_graph(district_roads, ax=ax, node_color=nc, filepath=img_url, save=True, show=False, close=True)
            maps.append("")
            maps.append(f"District {d}")
            maps.append(f"<img src=\"{img_url}\" alt=\"Driving connectivity map showing {partition_count} partitions for district {d}\" width=\"600px\">")
            d += 1

        if disconnected:
            disc_str = ", ".join([str(x) for x in disconnected])
            summary = f"This map *fails* because some districts ({disc_str}) have disconnected road networks. This means some folks would have to drive through another district to get to another place in their district."
        else:
            summary = "This map *passes* because all districts are connected. Meaning you can drive to anywhere in each district without leaving it."

        return ("Driving Connectivity", summary + "\n".join(maps), disconnected)

    def summarize(self, summaries):
        lines = []
        for stem, disconnected in summaries.items():
            if disconnected:
                multiple = "s" if len(disconnected) > 1 else ""
                disconnected = ", ".join([str(x) for x in disconnected])
                status = f"❌ District{multiple} {disconnected} disconnected"
            else:
                status = "✅"
            lines.append(f"* [{stem}](./{stem}.md) {status}")
        return "\n".join(lines)