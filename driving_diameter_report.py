# This script was used to filter the blocks from the block20 redistricting data (too big for github)
# for washington to seattle. Seattle was defined by existing districts plus a polygon to bridge the
# ship canal.

import geopandas
import pandas
import sys
import osmnx
import networkx
import sqlite3
import matplotlib.pyplot as plt
import time
from markdown_table_generator import generate_markdown, table_from_string_list

class DrivingDiameterReport:

    def __init__(self):
        blocks = geopandas.read_file("seattle_census_blocks/seattle_blocks.shp")
        self.roads = osmnx.load_graphml("sources/roads.graphml")
        self.roads = osmnx.project_graph(self.roads, blocks.crs)
        self.roads = self.roads.subgraph(max(networkx.strongly_connected_components(self.roads), key=len))
        
        edges = osmnx.graph_to_gdfs(self.roads, nodes=False)
        edge_types = edges['speed_kph'].value_counts()
        cutoff = 100
        too_small_types = edge_types[edge_types < cutoff]
        edge_types = edge_types[edge_types >= cutoff]
        edge_types = edge_types.index.tolist()
        color_list = osmnx.plot.get_colors(n=len(edge_types) + 1, cmap="rainbow")
        self.color_mapper = dict(zip(edge_types, color_list[1:]))
        for v in too_small_types.index:
            self.color_mapper[v] = color_list[0]
        self.edge_colors = [self.color_mapper[d['speed_kph']] for u, v, k, d in self.roads.edges(keys=True, data=True)]
        
        self.con = sqlite3.connect("shortest_path_cache.db")
        cur = self.con.cursor()
        cur.execute("CREATE INDEX IF NOT EXISTS travel_time_desc ON paths (travel_time DESC)")
        cur.execute("CREATE INDEX IF NOT EXISTS src ON paths (source)")
        cur.execute("CREATE INDEX IF NOT EXISTS dst ON paths (destination)")
        self.con.commit()
        self.nodes = osmnx.graph_to_gdfs(self.roads, edges=False)
        self.nodes = self.nodes[self.nodes["highway"] != "motorway_junction"]
        blocks = blocks[["GEOID20", "geometry"]]
        blocks["GEOID20"] = pandas.to_numeric(blocks["GEOID20"], errors='coerce').convert_dtypes()
        self.blocks = blocks[["GEOID20", "geometry"]]

    def content(self, districts, asset_directory=None):
        lines = []
        blocks = self.blocks.merge(districts, on="GEOID20")
        del blocks["GEOID20"]

        self.con.execute("ATTACH DATABASE ':memory:' AS dist;")

        cur = self.con.cursor();

        joined = blocks.dissolve(by="District")
        print(time.monotonic(), joined)

        ax = joined.boundary.plot(edgecolor="black", figsize=(9,16))
        # get the color for each edge based on its highway type
        osmnx.plot_graph(self.roads, edge_color=self.edge_colors, node_size=0, ax=ax, show=False)

        routes = []
        rows = [["District", "Max Travel Time (minutes)"]]
        for d, bounds in enumerate(joined["geometry"]):
            print(time.monotonic())
            cur.execute("CREATE TABLE dist.dm (node INTEGER PRIMARY KEY, district INTEGER)")

            intersecting_nodes = self.nodes[self.nodes.intersects(bounds.buffer(10))].index
            print(time.monotonic(), d+1)
            cur.executemany("INSERT INTO dist.dm (node, district) VALUES (?, ?)", ((n, d+1) for n in intersecting_nodes))
            print(time.monotonic(), "inserted")
            cur.execute("SELECT source, destination, travel_time FROM paths WHERE source IN (SELECT node FROM dist.dm) AND destination IN (SELECT node FROM dist.dm) ORDER BY travel_time DESC LIMIT 1")
            source, dest, travel_time = cur.fetchone()
            print(time.monotonic(), travel_time, "seconds", travel_time / 60, "minutes")
            rows.append([str(d+1), f"{travel_time / 60:0.2f}"])
            route = osmnx.shortest_path(self.roads, source, dest, weight="travel_time")
            print(time.monotonic(), "routed")
            routes.append(route)

            cur.execute("DROP TABLE dist.dm")
            self.con.commit()
            print()

        joined['coords'] = joined['geometry'].apply(lambda x: x.representative_point().coords[:])
        joined['coords'] = [coords[0] for coords in joined['coords']]
        for idx, row in joined.iterrows():
            plt.annotate(idx, xy=row['coords'],
                         horizontalalignment='center', fontsize="xx-large",
                         fontweight="bold")

        table = table_from_string_list(rows)
        markdown = generate_markdown(table)
        img_url = asset_directory / 'driving_diameter.png'
        fig, ax = osmnx.plot_graph_routes(self.roads, routes, ax=ax, filepath=img_url, save=True, show=False, close=True)
        self.con.execute("DETACH DATABASE dist;")

        img_url = str(img_url)[len("reports/"):]
        return ("Driving Diameter", f"<img src=\"{img_url}\" alt=\"Driving Diameter Map showing 7 routes\" width=\"600px\">\n\n" + markdown)
