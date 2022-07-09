import networkx
import osmnx
import sqlite3
import array

import rich.progress

con = sqlite3.connect("shortest_path_cache.db")

cur = con.cursor()

try:
    cur.execute("CREATE TABLE paths (source INTEGER, destination INTEGER, travel_time REAL, length REAL, PRIMARY KEY(source, destination))")
except sqlite3.OperationalError:
    pass
g = osmnx.load_graphml("sources/roads.graphml")

sg = g.subgraph(max(networkx.strongly_connected_components(g), key=len))
lengths = {}
p = rich.progress.Progress(rich.progress.BarColumn(bar_width=None), rich.progress.MofNCompleteColumn(), rich.progress.TimeRemainingColumn(), expand=True)
with p:
    for i, source in enumerate(p.track(sg.nodes)):
        times = networkx.single_source_dijkstra_path_length(sg, source, weight="travel_time")
        all_dests = []
        for dest in times:
            all_dests.append((source, dest, times[dest]))
        with con:
            con.executemany("INSERT INTO paths (source, destination, travel_time) values (?, ?, ?) ON CONFLICT (source, destination) DO UPDATE SET travel_time = excluded.travel_time, length = excluded.length", all_dests)
con.close()
