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

class DrivingDiameterReport:

    def __init__(self):
        blocks = geopandas.read_file("seattle_census_blocks/seattle_blocks.shp")
        self.roads = osmnx.load_graphml("sources/roads.graphml")
        self.roads = osmnx.project_graph(self.roads, blocks.crs)
        self.roads = self.roads.subgraph(max(networkx.strongly_connected_components(self.roads), key=len))
        
        edges = osmnx.graph_to_gdfs(self.roads, nodes=False)
        edge_types = edges['speed_kph'].value_counts()
        edge_types = edge_types.index.tolist()
        color_list = osmnx.plot.get_colors(n=len(edge_types))
        color_mapper = dict(zip(edge_types, color_list))

        # get the color for each edge based on its highway type
        ec = [color_mapper[d['speed_kph']] for u, v, k, d in self.roads.edges(keys=True, data=True)]

        osmnx.plot_graph(self.roads, edge_color=ec, node_size=0)
        self.con = sqlite3.connect("shortest_path_cache.db")
        cur = self.con.cursor()
        cur.execute("CREATE INDEX IF NOT EXISTS travel_time_desc ON paths (travel_time DESC)")
        cur.execute("CREATE INDEX IF NOT EXISTS src ON paths (source)")
        cur.execute("CREATE INDEX IF NOT EXISTS dst ON paths (destination)")
        self.con.commit()
        self.nodes = osmnx.graph_to_gdfs(self.roads, edges=False)
        blocks = blocks[["GEOID20", "geometry"]]
        blocks["GEOID20"] = pandas.to_numeric(blocks["GEOID20"], errors='coerce').convert_dtypes()
        self.blocks = blocks[["GEOID20", "geometry"]]

    def content(self, districts):
        lines = []
        blocks = self.blocks.merge(districts, on="GEOID20")
        del blocks["GEOID20"]

        self.con.execute("ATTACH DATABASE ':memory:' AS dist;")

        cur = self.con.cursor();

        joined = blocks.dissolve(by="District")
        print(time.monotonic(), joined)
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
            route = osmnx.shortest_path(self.roads, source, dest, weight="travel_time")
            print(time.monotonic(), route)
            district_roads = self.roads.subgraph(intersecting_nodes.tolist() + route)
            ax = joined[joined["geometry"]==bounds].boundary.plot(edgecolor="black")
            ec = osmnx.plot.get_edge_colors_by_attr(district_roads, attr="speed_kph")
            osmnx.plot_graph(district_roads, ax=ax, edge_color=ec, show=False, node_size=0)
            print(time.monotonic(), "plot")
            osmnx.plot_graph_route(district_roads, route, ax=ax)

            cur.execute("DROP TABLE dist.dm")
            self.con.commit()
            print()
        self.con.execute("DETACH DATABASE dist;")

DrivingDiameterReport()

