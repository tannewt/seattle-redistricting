import osmnx

g = osmnx.graph_from_place("Seattle, WA", network_type='drive')
g = osmnx.add_edge_speeds(g)
g = osmnx.add_edge_travel_times(g)
osmnx.save_graphml(g, "sources/roads.graphml")
